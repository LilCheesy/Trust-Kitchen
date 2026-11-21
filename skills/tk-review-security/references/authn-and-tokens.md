# Authentication, sessions and tokens

- **Passwords.** Hash with a slow, salted algorithm (argon2, bcrypt, scrypt). Compare in constant time. Never log
  them, and never send them back to the client.
- **Sessions.** Use random ids from a secure generator, rotate them on login and privilege change, and invalidate
  them on logout and password change. Cookies are `HttpOnly`, `Secure` and have a `SameSite` setting.
- **JWT.** Verify the signature with a fixed algorithm allowlist (no `none`, no algorithm taken from the header).
  Check `exp`, `nbf`, `aud` and `iss`. Keys come from config, not code. Do not put sensitive data in claims; they
  are readable. Revocation is planned for long-lived tokens.
- **OAuth / OIDC.**
  - Check `state` (CSRF) and PKCE for public clients.
  - Redirect URIs are exact-match, never prefix or regex.
  - Validate the ID token (signature, audience, nonce).
  - Never accept an access token issued for another client.
- **SAML.** Validate the signature on the assertion actually used. Watch for XML signature wrapping, and check
  audience, recipient and time windows. Use a maintained library.
- **Password reset / magic links.** Tokens are single-use, short-lived, random, and bound to the account. Responses
  do not reveal whether an account exists. Old tokens die when a new one is issued.
- **MFA.** It cannot be skipped by calling the next step directly. Rate-limit code attempts. Backup codes are
  single-use and hashed.
- **Brute force.** Rate limits and lockout or backoff on login, reset, OTP and invite endpoints.
- **API keys.** Scoped, revocable, stored hashed, shown once.

Common slop here: commented-out checks "for testing", `verify=False`, `algorithms` read from the token, or
`if DEBUG: skip_auth`.
