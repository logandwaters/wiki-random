
Defaults are intentionally broad and conservative. Users are encouraged to narrow results via categories, min_size, evergreen, and keyword filters.

May still runturn undesireable artiles, lists, indexes, etc. 

Sticter filters may cause higher probability of repeats or failures to find adequatearticles.



# Wiki Random API

A small, self-hosted HTTP API that redirects you to a random, readable Wikipedia article based on configurable interest categories.

Designed to be:
- Stateless
- Lightweight
- Bookmark-friendly
- Safe to expose publicly

This project intentionally avoids UI or frontend concerns. It is meant to be used directly via a browser, shortcut, or automation tool.

---

## Core Endpoint

```
GET /api/wiki-random
```

Redirects (`302`) to a Wikipedia article.

### Default Behavior

If no parameters are supplied, the API:
- Selects a random article
- From broad, general-interest categories
- Ensures a minimum article size
- Avoids disambiguation and low-quality pages by pulling from the "0" namespace and light filtering

---

## Query Parameters

### `categories` (optional)

Comma-separated list of Wikipedia categories.

Example:
```
?categories=Technology,Physics,Mathematics
```

If omitted, defaults to:
- Technology
- Science
- Engineering
- Computer science
- Internet
- Mathematics
- Physics
- Biology
- Economics
- Psychology

---

### `min_size` (optional)

Minimum article size in bytes.

Example:
```
?min_size=8000
```

Default:
```
6000
```

---

### `evergreen` (optional)

Filters out time-sensitive or list-style articles.

Accepted values:
- `true`
- `false` (default)

When enabled, the API attempts to exclude:
- Articles containing years (e.g. “2021”)
- Lists, timelines, outlines
- Event-based or news-style topics

Example:
```
?evergreen=true
```

This logic is heuristic-based and intentionally conservative.

---

### `exclude` (optional)

Comma-separated list of keywords to exclude from results.

The filter applies to:
- Article titles
- Wikipedia search snippets

Matching is case-insensitive and substring-based.

Example:
```
?exclude=politics,election,government
```

This parameter is intended for personal preference filtering, not content moderation.

---

## Health Check

```
GET /api/wiki-random/health
```

Returns a simple JSON response for uptime and monitoring checks.

Example response:
```json
{
  "status": "ok",
  "service": "wiki-random-api"
}
```

---

## Rate Limiting

A lightweight in-memory throttle is applied per IP:

- 30 requests per minute
- Sliding window
- No persistence (resets on restart)

Exceeding the limit returns:
```
HTTP 429 Too Many Requests
```

This is intended as basic protection, not a security boundary.

---

## Failure Semantics

The API:
- Retries Wikipedia API calls internally
- Attempts multiple categories before failing
- Returns structured JSON errors for non-redirect outcomes

Possible error responses:
- `429` – Rate limit exceeded
- `502` – No suitable article found after retries

---

## Deployment Notes

- Designed for reverse-proxy usage (Traefik, Nginx, Cloudflare Tunnel)
- Path-based routing supported (`/api/wiki-random`)
- Stateless; safe to scale horizontally

### Recommended Headers
- Set `X-Forwarded-For` correctly at the proxy level
- Customize `User-Agent` if hosting publicly

---

## Intended Use

Typical use cases:
- Browser bookmarks
- Mobile shortcuts
- Daily “learn something new” automations
- Personal dashboards or tooling

This project prioritizes simplicity, clarity, and robustness over features.

---

## License

MIT (or your preferred permissive license)
