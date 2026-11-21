# Supply chain, CI and infrastructure

- **New dependencies.**
  - Is it the package you meant? Check for typosquats and names that look alike.
  - Is it maintained? What licence does it have? Is the version pinned, and does the lockfile change?
  - Does it run install scripts?
  - Prefer the standard library or an existing dependency over adding a new one for a few lines of code.
- **Lockfiles.** A large lockfile churn without a matching manifest change needs an explanation.
- **CI workflows.**
  - Third-party actions are pinned to a commit SHA, not a tag.
  - Untrusted PR code never runs with secrets: watch `pull_request_target` with a checkout of the PR head.
  - `${{ github.event.* }}` is never interpolated into `run:` shells, because that is script injection.
  - Tokens are least-privilege (`permissions:` set).
  - Artifacts and caches cannot be poisoned across branches.
- **Containers.**
  - Base images are pinned (digest), not `latest`.
  - Containers do not run as root and do not get `--privileged` or extra capabilities.
  - No secrets in image layers or build args.
  - Ports are only exposed when needed.
- **Kubernetes / IaC.**
  - No `privileged`, `hostNetwork` or `hostPath` without a reason.
  - Resource limits are set; service accounts are least-privilege.
  - Storage buckets are not public by default.
  - Security groups do not allow `0.0.0.0/0` on admin ports.
  - IAM policies avoid `*:*`.
- **Build reproducibility.** Downloads during build are checksummed. `curl … | sh` in a Dockerfile or script is a
  finding.

All of these are restricted areas for the merge gate: a person reviews them.
