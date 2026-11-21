# Injection

Untrusted data must never become **code** or **structure** in another language.

| Kind | Dangerous in a diff | Safe pattern |
|---|---|---|
| SQL | string formatting or concatenation into a query; `raw()` / `execute(f"...")`; dynamic `ORDER BY` / table names from input | parameters / bind variables; allowlist for identifiers |
| NoSQL | user JSON passed as a query object (`$where`, `$ne`, operators); `eval`-style queries | build queries from typed fields; reject operator keys |
| OS command | `shell=True`, `os.system`, backticks, `exec` with a joined string | argument lists, no shell; allowlist of commands; `--` before user paths |
| Code | `eval`, `exec`, `Function()`, `setTimeout(string)`, dynamic `import` of user names | never evaluate input; dispatch via a mapping |
| Template (SSTI) | user input used as the template itself; `render_template_string(user)` | user input only as template **data**; autoescape on |
| LDAP / XPath | filters built by string concatenation | library escaping functions |
| XML (XXE) | parsers with external entities or DTDs enabled | disable DTDs / external entities; defusedxml-style parsers |
| Regex (ReDoS) | user-supplied patterns; nested quantifiers on user text `(a+)+` | no user patterns; linear-time engines or timeouts |
| Header / log | CR/LF from input into headers or log lines | reject control characters; structured logging |

**Trace:** find the source (request, file, message, DB value that a user controls), then the sink, then every
transformation between them. Escaping for the wrong context (HTML escaping before SQL) does not count.
