# Flock Energy API Wrapper

This project wraps the legacy Urja Meter Ops web application with a clean FastAPI layer. It authenticates with the live SvelteKit portal, preserves cookies, and normalizes HTML-heavy responses into JSON payloads for downstream clients.

## Features

- Session-based authentication against the portal
- Same-origin login flow handling for SvelteKit CSRF protection
- HTML parsing with BeautifulSoup for meter listings and detail pages
- REST endpoints exposed via FastAPI with OpenAPI docs
- Safe normalization for empty or partially populated legacy pages

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API endpoints

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/meters`
- `GET /api/v1/meters/{meter_id}`
- `GET /api/v1/meters/{meter_id}/consumption`
- `GET /api/v1/hierarchy`
- `GET /openapi.json`
- `GET /docs`

## Example requests

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"operator@urja.local","password":"urja-ops-2026"}'
```

### List meters

```bash
curl "http://localhost:8000/api/v1/meters?page=1&page_size=25"
```

### Meter detail

```bash
curl "http://localhost:8000/api/v1/meters/ABC123"
```

### Consumption history

```bash
curl "http://localhost:8000/api/v1/meters/ABC123/consumption?days=30"
```

## Notes on the legacy portal

The upstream app is a SvelteKit-based portal with a `POST /login` form. Access is guarded by same-origin checks. The feasible automation flow is:

1. GET `/login`
2. Preserve the session cookie and browser-like headers
3. POST `email` and `password` with `Origin` and `Referer` set to the portal domain
4. Continue using the authenticated session for `/meters` and detail pages

Because the portal does not expose a clean JSON API in the browser source, this adapter deliberately treats HTML as the source of truth and normalizes it into JSON responses.

## Intentional trade-offs

- The project does not pretend to be a full replacement for the legacy app; it is a thin proxy.
- It avoids fragile browser automation and instead uses session cookies plus HTML parsing.
- Some fields may be missing when the legacy UI renders sparse states (for example, an empty meter list).

## Security note

The credentials are intentionally taken from the assignment and are only used to demonstrate the legacy-session workflow.
