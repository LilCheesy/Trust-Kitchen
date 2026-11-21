# LLM features, agents, RAG and model pipelines

Text an LLM reads is an attack surface. Treat model output as untrusted input.

## Prompt injection

- Content from users, documents, web pages, emails, tickets, diffs or tool results is **data**. It must never be
  able to change the system's instructions, tool permissions or approval decisions.
- Check for:
  - untrusted text concatenated into a system prompt;
  - "summarise this page" flows where the page can trigger tools;
  - review bots that can be told to approve.
- Mitigations: keep instructions and data in separate roles or channels, run allowlisted tools, and use a
  confirmation step for consequential actions. **Assume injection will sometimes succeed** and limit what a
  successful one can do.

## Tools and agents

- **Least privilege.** Each tool does one thing, with scoped credentials. The agent cannot widen its own
  permissions, approve its own actions or edit its own guardrails.
- **Consequential actions** need a person or a separate approver: payments, sending messages, deleting, merging,
  deploying, data export.
- **Model output into code paths.** Output used in SQL, a shell, file paths, URLs or HTML is injection-prone.
  Apply `injection.md`.
- **Loops and cost.** Set limits on steps, tokens, time and spend, and stop cleanly when one is reached.

## RAG and memory

- Retrieval respects the **caller's** permissions. One tenant's documents must not reach another tenant's answers,
  and the vector store is filtered by access control, not only by similarity.
- Ingested documents can carry injections. Mark the source and trust level of each retrieved chunk.
- Memory written by the agent can be poisoned. Check who and what can write to it.

## Data and model pipelines

- **Training and fine-tuning data.**
  - Record where it came from and its licence.
  - No personal or customer data without a legal basis.
  - Check for poisoning: unexpected sources, label flips, outliers.
  - Keep a hash of each dataset version.
- **Model files.** Pickle-based weight formats execute code on load. Prefer safe formats such as safetensors, and
  load only models from verified sources with recorded hashes.
- **Evaluation integrity.** Test sets never leak into training. Thresholds are fixed **before** the run.
- **Outputs.** Check whether outputs can leak training data (memorised secrets or personal data).
