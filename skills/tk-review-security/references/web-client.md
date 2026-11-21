# Browser-facing risks

- **XSS.** Untrusted data reaches `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `document.write`, template
  `|safe` / `{{{ }}}`, `href="javascript:"` or event-handler attributes without context-correct encoding. Prefer text
  APIs and framework escaping. Sanitise rich HTML with a maintained sanitiser. Check DOM-based flows from
  `location`, `postMessage` or `localStorage` too.
- **CSRF.** State-changing requests authenticated by cookies need `SameSite`, CSRF tokens or origin checks. `GET`
  must not change state.
- **CORS.** Never reflect an arbitrary `Origin` with `Access-Control-Allow-Credentials: true`. Avoid wildcard
  origins on authenticated APIs. Check how `null` origin and regex origins are handled.
- **Open redirect.** Redirect targets from input go through an allowlist or a relative-path check (and beware
  `//evil.example`).
- **Clickjacking.** Sensitive pages send `frame-ancestors` (CSP) or `X-Frame-Options`.
- **Security headers.** Do not remove CSP, HSTS or `X-Content-Type-Options: nosniff`. Serve user files with a safe
  content type and `Content-Disposition` where appropriate.
- **postMessage.** Check `event.origin` and send to an exact target origin.
- **Client-side checks.** Hiding a button is not authorization; the server must refuse.
