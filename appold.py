
import random
import re
import time
import logging
import requests
from collections import defaultdict, deque
from flask import Flask, redirect, jsonify, request

app = Flask(__name__)

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ---------------- Constants ----------------
WIKI_API = "https://en.wikipedia.org/w/api.php"

DEFAULT_MIN_PAGE_SIZE = 6000

# Broader, general-interest defaults (overridable via query params)
DEFAULT_CATEGORIES = [
    # Science & Engineering
    "Science",
    "Technology",
    "Engineering",
    "Computer science",
    "Mathematics",
    "Physics",
    "Biology",
    "Chemistry",

    # Society & Thought
    "Psychology",
    "Philosophy",
    "Sociology",
    "Economics",
    "Education",

    # History & Geography
    "World history",
    "Geography",
    "Ancient history",
    "Modern history",

    # Culture & Arts
    "Art",
    "Architecture",
    "Music",
    "Literature",
    "Film",

    # Practical & Applied
    "Medicine",
    "Health",
    "Business",
    "Entrepreneurship",
    "Design",

    # Nature & Environment
    "Ecology",
    "Earth sciences",
    "Astronomy"
]

HEADERS = {
    "User-Agent": "WikiRandomAPI/1.3 (self-hosted; contact: admin@local)"
}

# Retry / timeout behavior
REQUEST_TIMEOUT = 8
MAX_RETRIES = 3

# Throttle (simple in-memory, per-IP)
RATE_LIMIT = 30          # requests
RATE_WINDOW = 60         # seconds
_request_log = defaultdict(deque)

# ---------------- Utilities ----------------

def rate_limited(ip: str) -> bool:
    now = time.time()
    window = _request_log[ip]

    while window and window[0] < now - RATE_WINDOW:
        window.popleft()

    if len(window) >= RATE_LIMIT:
        return True

    window.append(now)
    return False


def wiki_request(params: dict) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(
                WIKI_API,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logging.warning("Wiki request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt == MAX_RETRIES:
                raise


def fetch_candidates(category: str) -> list:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f'incategory:"{category}"',
        "srnamespace": 0,
        "srlimit": 20,
        "srprop": "size",
        "format": "json"
    }
    data = wiki_request(params)
    return data.get("query", {}).get("search", [])


def is_non_evergreen(title: str) -> bool:
    title_lower = title.lower()

    # Year-based titles
    if re.search(r'\b(19|20)\d{2}\b', title):
        return True

    # Time-sensitive or list-style articles
    if title_lower.startswith((
        "list of",
        "timeline of",
        "history of",
        "outline of"
    )):
        return True

    # Event-oriented language
    if any(word in title_lower for word in ["conference", "election", "incident", "scandal"]):
        return True

    return False


def contains_excluded_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

# ---------------- Routes ----------------

@app.route("/api/wiki-random")
def random_article():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if rate_limited(client_ip):
        logging.warning("Rate limit exceeded | IP: %s", client_ip)
        return jsonify({"error": "rate limit exceeded"}), 429

    categories_param = request.args.get("categories")
    min_size_param = request.args.get("min_size")
    evergreen_param = request.args.get("evergreen", "false").lower()
    exclude_param = request.args.get("exclude")

    evergreen = evergreen_param == "true"

    # Categories
    if categories_param:
        categories = [c.strip() for c in categories_param.split(",") if c.strip()]
        if not categories:
            categories = DEFAULT_CATEGORIES
    else:
        categories = DEFAULT_CATEGORIES

    # Minimum size
    try:
        min_size = int(min_size_param) if min_size_param else DEFAULT_MIN_PAGE_SIZE
    except ValueError:
        min_size = DEFAULT_MIN_PAGE_SIZE

    attempts = 0
    max_attempts = len(categories) * 2

    while attempts < max_attempts:
        attempts += 1
        category = random.choice(categories)

        try:
            results = fetch_candidates(category)
        except Exception:
            continue

        valid = [
            page for page in results
            if page.get("size", 0) >= min_size
            and "disambiguation" not in page.get("title", "").lower()
            and (not evergreen or not is_non_evergreen(page.get("title", "")))
            and not contains_excluded_keyword(
                page.get("title", "") + " " + page.get("snippet", ""),
                exclude_keywords
            )
        ]

        if valid:
            article = random.choice(valid)
            title = article["title"].replace(" ", "_")
            url = f"https://en.wikipedia.org/wiki/{title}"

            logging.info(
                "Redirect | Title='%s' | Category='%s' | MinSize=%d | Evergreen=%s | Exclude=%s | IP=%s",
                article["title"], category, min_size, evergreen, exclude_keywords or "none", client_ip
            )

            return redirect(url, code=302)
    
    # Exclude by keyword
    if exclude_param:
        exclude_keywords = [
            kw.strip().lower() for kw in exclude_param.split(",") if kw.strip()
        ]
    else:
        exclude_keywords = []

    logging.error(
        "No article found | Categories=%s | MinSize=%d | Evergreen=%s | IP=%s",
        categories, min_size, evergreen, client_ip
    )

    return jsonify({"error": "no suitable article found"}), 502


@app.route("/api/wiki-random/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "wiki-random-api"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)