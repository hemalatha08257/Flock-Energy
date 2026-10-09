# Reflection

## 1. What assumptions did we make about the legacy portal?

We assumed the legacy app would continue to use a same-origin session cookie mechanism and that no hidden JSON API would be available without browser-like auth headers. Because the HTML source showed a SvelteKit login form and table-based rendering, we chose to treat the portal as an HTML-backed stateful app rather than a formal JSON service.

## 2. What was the most difficult part of this project?

The hardest part was reversing the authentication flow. The app rejects cross-site POST requests, so the adapter had to emulate browser headers like `Origin` and `Referer` and preserve the `__Secure-better-auth.session_token` cookie. Once that was understood, the rest of the API wrappers were straightforward.

## 3. What mistakes or false starts happened?

The first pass tried to treat the login as a plain form POST without browser-like headers. That failed with the SvelteKit cross-site protection message. A second pass used the correct same-origin headers and session cookie handling, which worked against the live app.

## 4. What would you improve in a real production version?

I would add a more robust retry and re-auth strategy, a TTL-based session manager, and explicit parsing for real meter detail and consumption fields when the UI has actual data. I would also isolate the portal parsing into more specific selectors and include a caching layer to reduce repeated page fetches.

## 5. What did this project teach us about legacy integration work?

Legacy integration is rarely clean by default. The portal exposes a usable browser flow, but the data is fragmented across HTML and server-rendered pages. A resilient integration layer needs session persistence, tolerant parsing, and clear fallbacks when the underlying app is sparse or inconsistent.
