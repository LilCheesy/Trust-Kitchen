# Business logic and race conditions

Scanners rarely find these. Read the rule, then try to break it with inputs a normal user can send.

- **Money and quantities.**
  - Negative or zero amounts, rounding direction, currency mixing, and overflow.
  - Floats used for money. Use integers in the smallest unit, or decimals.
  - Discounts that stack, and refunds larger than the payment.
- **State machines.**
  - Can a step be skipped by calling the next endpoint directly?
  - Can a finished order or a cancelled subscription be changed?
  - Can an approval be reused?
- **Limits and quotas.** Are limits enforced on the server, per tenant or user, **atomically**? A check followed by
  a separate write lets two parallel requests both pass.
- **Races (check-then-act).** Balance checks, coupon use, invite acceptance, inventory, unique usernames. Use
  database constraints, transactions with the right isolation, row locks or atomic updates (`UPDATE … WHERE
  balance >= x`). Idempotency keys for retries.
- **Time.** Time zones, daylight saving and expiry, all compared in UTC. Clocks taken from the client are
  untrusted.
- **Enumeration.** Sequential ids, and timing or error differences, reveal whether a user exists.
- **Abuse.** Expensive operations (exports, reports, model calls) need rate limits and quotas.

Proof: a test that fires the same request twice concurrently, or that calls step 3 before step 2, and asserts
the business rule still holds.
