# Access control (IDOR, privilege escalation, multi-tenancy)

The most common serious bug in business software: the code checks **that** you are logged in, not **whether this
object is yours**.

Check in the diff:
- **Every object read or write by id** (`/orders/{id}`, `?user_id=`, GraphQL node ids, file keys) has a server-side
  ownership or tenant check **on that object**. Listing endpoints filter by the caller's tenant or ownership.
- **Ids from the client are not trusted.** `user_id`, `tenant_id`, `role`, `is_admin`, `price` and `owner`
  in a request body must be ignored or verified against the session.
- **New endpoints / actions** declare the permission they need; the check lives in one place (middleware,
  decorator, policy), not copied per handler. Look for handlers that forgot it.
- **Admin and internal paths** are not protected only by being hidden or by client-side checks.
- **Self-approval and separation of duties.** The requester cannot approve their own request, refund, merge or
  role change.
- **Mass assignment.** Binding a whole request body onto a model can let callers set protected fields.
- **Tenant isolation.** Caches, background jobs, exports, search indexes and file stores are scoped by tenant too,
  not only the main query.
- **Failure mode.** Unknown role or missing permission means **deny**.

Proof: a test where user A requests user B's object and must get 403/404. If no such test exists for a new
endpoint, that is a MAJOR finding.
