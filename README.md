
# Wiki Random API

A lightweight, stateless HTTP API that redirects users to a random, readable Wikipedia article based on configurable interests.

Designed for:
- Browser bookmarks
- Mobile shortcuts
- Automations
- Personal learning tools

---

## Endpoint

```
GET /api/wiki-random
```

Returns a **302 redirect** to a Wikipedia article.

---

## Query Parameters

### categories
Comma-separated list of Wikipedia categories.

```
?categories=Science,Technology,Art
```

Defaults to broad, general-interest categories.

---

### min_size
Minimum article size in bytes.

```
?min_size=8000
```

Default: `6000`

---

### evergreen
Attempts to filter time-sensitive or list-style articles.

```
?evergreen=true
```

Heuristic-based and conservative.

---

### exclude
Comma-separated keywords to exclude (case-insensitive).

```
?exclude=politics,election,government
```

Applied to titles and snippets.

---

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

---

## License

This project is licensed under the  
**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license.

You are free to:
- Use and modify the code for personal or educational purposes
- Share and collaborate on non-commercial forks

You may not:
- Use this project or derivatives for commercial purposes
- Offer it as a paid service or product

Full license text: https://creativecommons.org/licenses/by-nc/4.0/