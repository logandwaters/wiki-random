# Wiki Random API
## Development & Personally Deployment Notes

The wiki-random API is a small, self-hosted HTTP API that redirects users to a random, readable Wikipedia article based on configurable interest categories.

It is designed to be:
- Stateless
- Lightweight
- Bookmark-friendly
- Safe to expose publicly
- Respectfully use Wikipedia's api resource

This project intentionally uses an API only approach for simplicity. It is meant to accessed by humans only, directly accessed via a browser, shortcut, or command line request.

---

# Options
## Endpoints

Method | Slug | Description
GET | /api/wiki-random | Redirects (`302`) to a random Wikipedia article
GET | /api/wiki-random/health | Health check endpoint, returns JSON status

## Query Parameters

Parameter | Type | Default | Description | Use
categories | string (CSV) | [Categories default](#ADD_DEFAULT_CATEGORIES_HERE) | Comma-separated list of Wikipedia categories to source articles from | `?categories=science,technology,art`
min_size | integer | 6000 | Minimum article size in bytes | `?min_size=8000`
evergreen | boolean | false | Attempts to filter out time-sensitive or list-style articles | `?evergreen=true`
exclude | string (CSV) | none | Comma-separated list of keywords to exclude from results | `?exclude=politics,election`

Defaults are intentionally broad and conservative. Users are encouraged to narrow results via categories, min_size, evergreen, and keyword filters. Excessively strict filters may lead to higher probability of repeats or failures to find adequate articles.

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

## Health Check

```
GET /api/wiki-random/health
```

Returns:

```json
{ "status": "ok", "service": "wiki-random-api" }
```

---

## Rate Limiting

- 30 requests per IP per minute
- In-memory sliding window
- Returns HTTP 429 on excess

---

## Deployment

- Run behind Traefik, Nginx, or Cloudflare Tunnel
- HTTPS handled by proxy
- Path-based routing supported

---

## Philosophy

This project prioritizes:
- Simplicity
- Predictable behavior
- Robust failure handling

It intentionally avoids UI and persistence.

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

Defaults are intentionally broad and conservative. Users are encouraged to narrow results via categories, min_size, evergreen, and keyword filters.