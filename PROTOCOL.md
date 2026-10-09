# Protocol discovery for Urja Meter Ops

## Authentication workflow

The legacy app is served by a SvelteKit frontend at `https://urja-ops.flockenergy.tech`.

Observed flow:

1. `GET https://urja-ops.flockenergy.tech/login` returns the sign-in page.
2. The form is a regular HTML `POST` with fields `email` and `password`.
3. The site blocks cross-site form posts with the message `Cross-site POST form submissions are forbidden`.
4. The working automation pattern is to send the request with browser-like headers:
   - `Origin: https://urja-ops.flockenergy.tech`
   - `Referer: https://urja-ops.flockenergy.tech/login`
   - `User-Agent: Mozilla/5.0 ...`
5. A successful login sets the session cookie `__Secure-better-auth.session_token`.
6. The response contains a `303` redirect to `/meters`, which matches the app’s navigation flow.

## URL inventory

- `GET /login` — sign-in form
- `POST /login` — email/password auth
- `GET /meters` — meter listing page
- `GET /transformers` — transformer/hierarchy page (when available)
- `GET /meters/{id}` — meter detail page
- `GET /meters/{id}/consumption` — consumption page (when implemented)

## Data observations

- The portal is a server-rendered HTML application, not a clean JSON API.
- A page can render an empty state (`No meters found.`) without exposing any data records.
- The app uses table-based rendering on the listing pages, which makes it feasible to scrape structured rows with BeautifulSoup.
- The actual production UI does not reveal obvious public API endpoints in the HTML source, so the adapter treats HTML as the canonical input and normalizes it into JSON.

## Normalization strategy

The client layer intentionally does the following:

- keeps the session cookie as a long-lived object in the `httpx.Client`
- re-authenticates when the session token disappears or a 401 is returned
- filters empty rows and converts strings to consistent normalized fields
- returns empty arrays instead of crashing when legacy pages are blank

## Implementation assumptions

This project assumes the portal remains accessible from the same origin and that the assignment credentials continue to work. Where the upstream page does not provide a value, the API returns `null`/empty data rather than failing the whole response.
