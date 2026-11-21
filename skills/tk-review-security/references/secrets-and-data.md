# Secrets, logging and personal data

- **No secrets in the repository.** This covers code, config, fixtures, notebooks, docker files and CI files. Once
  committed, a secret is leaked: **rotate it**. Deleting the line is not enough.
- **Where secrets live.** Environment variables, a secret manager, or mounted files with restrictive permissions.
  Also check examples and defaults: `password: changeme` shipped as a working default is a finding.
- **Logs and errors.**
  - Never log tokens, passwords, full card numbers, session cookies, authorization headers or whole request bodies
    on auth paths.
  - Error responses do not include stack traces, SQL or internal hostnames in production.
- **Personal data.** A new field, log or export holding personal data needs a reason, an access check and a
  retention period. Minimise it: do not store what you do not need.
- **Encryption.** Use TLS for data in transit (no `verify=False`). Use encryption at rest for sensitive stores.
  Use standard libraries, never home-made crypto, and get randomness from a secure generator (not
  `random` / `Math.random` for tokens).
- **Analytics and third parties.** New SDKs and trackers send data off-site. Check what they send.
- **Test data.** Use synthetic or anonymised data only. Real customer data in tests or fixtures is a BLOCKER.
