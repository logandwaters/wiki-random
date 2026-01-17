import random
import re
import time
import logging
import requests
from collections import defaultdict, deque
from flask import Flask, redirect, jsonify, request

app = Flask(__name__)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Constants
WIKI_API = "https://en.wikipedia.org/w/api.php"

DEFAULT_MIN_PAGE_SIZE = 6000

DEFAULT_CATEGORIES = [
    "Science","Technology","Engineering","Computer science","Mathematics",
    "Physics","Biology","Chemistry","Psychology","Philosophy","Sociology",
    "Economics","Education","World history","Geography","Ancient history",
    "Modern history","Art","Architecture","Music","Literature","Film",
    "Medicine","Health","Business","Entrepreneurship","Design",
    "Ecology","Earth sciences","Astronomy"
]

HEADERS = {
    "User-Agent": "WikiRandomAPI/1.4 (self-hosted; contact: admin@local)"
}

REQUEST_TIMEOUT = 8
MAX_RETRIES = 3

RATE_LIMIT = 30
RATE_WINDOW = 60
_request_log = defaultdict(deque)

# Utilities

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
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
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
    t = title.lower()
    if re.search(r'\b(19|20)\d{2}\b', title):
        return True
    if t.startswith(("list of","timeline of","history of","outline of")):
        return True
    if any(w in t for w in ["conference","election","incident","scandal"]):
        return True
    return False


def contains_excluded_keyword(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(k in text for k in keywords)

# Routes

@app.route("/api/wiki-random")
def random_article():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if rate_limited(client_ip):
        logging.warning("Rate limit exceeded | IP=%s", client_ip)
        return jsonify({"error": "rate limit exceeded"}), 429

    # Params
    categories_param = request.args.get("categories")
    min_size_param = request.args.get("min_size")
    evergreen = request.args.get("evergreen", "false").lower() == "true"
    exclude_param = request.args.get("exclude")

    exclude_keywords = [
        kw.strip().lower() for kw in exclude_param.split(",") if kw.strip()
    ] if exclude_param else []

    categories = (
        [c.strip() for c in categories_param.split(",") if c.strip()]
        if categories_param else DEFAULT_CATEGORIES
    ) or DEFAULT_CATEGORIES

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
            p for p in results
            if p.get("size", 0) >= min_size
            and "disambiguation" not in p.get("title","").lower()
            and (not evergreen or not is_non_evergreen(p.get("title","")))
            and not contains_excluded_keyword(
                p.get("title","") + " " + p.get("snippet",""),
                exclude_keywords
            )
        ]

        if valid:
            article = random.choice(valid)
            title = article["title"].replace(" ","_")
            url = f"https://en.wikipedia.org/wiki/{title}"

            logging.info(
                "Redirect | Title='%s' | Category='%s' | MinSize=%d | Evergreen=%s | Exclude=%s | IP=%s",
                article["title"], category, min_size, evergreen,
                exclude_keywords or "none", client_ip
            )
            return redirect(url, code=302)

    logging.error(
        "No article found | Categories=%s | MinSize=%d | Evergreen=%s | Exclude=%s | IP=%s",
        categories, min_size, evergreen, exclude_keywords or "none", client_ip
    )
    return jsonify({"error": "no suitable article found"}), 502


@app.route("/api/wiki-random/health")
def health():
    return jsonify({"status":"ok","service":"wiki-random-api"}), 200