# SSRF and outbound requests

Whenever the server fetches a URL or connects to a host that a user can influence (webhooks, previews, importers,
avatar fetchers, PDF renderers, proxies), check:

- **Allowlist over denylist.** Allowed schemes (`https`), hosts and ports. Denylists of "internal IPs" are easy to
  bypass with alternative IP encodings, IPv6, DNS that resolves internally, or redirects.
- **Resolve, then check, then connect to the checked address.** Otherwise DNS rebinding swaps the address between
  check and use.
- **Redirects.** Either disabled, or re-checked at every hop.
- **Metadata endpoints.** Cloud metadata addresses (`169.254.169.254`, `fd00:ec2::254` and similar) must be
  unreachable from fetchers.
- **Response handling.** Size and time limits, and no reflecting raw internal responses to the user.
- **Egress in code paths that should not need the network at all.** Libraries or new code that "phone home" can
  be caught by runtime proof: `tk-verify-network`.

Proof: a unit test that feeds `http://169.254.169.254/`, `http://localhost:…`, an internal hostname and a
redirecting URL, and expects rejection.
