---
name: tk-verify-network
description: Prove what a program or job actually sends over the network - write the allowlist first, plant a canary secret, run in a sandbox with packet capture, extract destinations, and check them and the canary with a script. Use when a change adds network calls, new dependencies or SDKs, telemetry, or when asked "does this phone home", "does it leak data", "verify egress", "what hosts does it call".
---

# Verify network behaviour

"The code doesn't send anything" is a claim. A packet capture is evidence.

## When to use

- The change adds HTTP clients, SDKs, telemetry or analytics, webhooks, or new dependencies.
- A job must reach the network (package installs, external APIs) and you need to bound it.

Do not use a capture when the job needs **no** network. Run it with networking disabled
(`docker run --network none …`) and treat any network error as a finding.

## Inputs

- The job or test command, and a container image for it.
- The list of hosts the job is expected to contact, each with a reason.
- An image or host with `tcpdump` and `tshark`.

## Procedure

1. **Write the allowlist first**, before running, as `allow.json`:

   ```json
   {"hosts": ["api.example.com", "*.pythonhosted.org", "10.0.0.0/8"], "ports": [443, 53]}
   ```

2. **Plant a canary.** Put a unique fake secret, `TK_CANARY=TK-CANARY-<random>`, in the job's environment and
   files. It must never leave the box.
3. **Run with capture,** on an isolated network, with the capture container sharing the job's network namespace:

   ```
   docker run -d --name job --network <isolated-net> -e TK_CANARY=… <image> <command>
   docker run --rm --net container:job -v "$PWD:/cap" <image-with-tcpdump> tcpdump -i any -w /cap/run.pcap
   ```

   Stop the capture when the job ends.
4. **Extract and check:**

   ```
   tshark -r run.pcap -T fields -e ip.dst -e tcp.dstport -e tls.handshake.extensions_server_name > fields.tsv
   tshark -r run.pcap -Y 'frame contains "TK-CANARY"' -x > payload.txt
   python .trust-kitchen/scripts/net_check.py --fields fields.tsv --allow allow.json --payload payload.txt --canary TK-CANARY-<random>
   ```

   Also list DNS queries (`-e dns.qry.name`) to see names that were looked up but not contacted.
5. **Report** the destinations (each allowed or not), the canary result, and the capture's sha256. Delete the
   capture after review; it can hold secrets or personal data.

## Output

```
Connections: <n> · unexpected: <host:port list | none> · canary: leaked | not seen
Capture: run.pcap sha256 <…> (kept locally, deleted after review)
Not covered: <code paths not exercised; TLS payloads not inspected>
```

## Rules

- MUST write the allowlist before running, never after looking at the traffic.
- NEVER commit or upload capture files.
- MUST state that TLS hides payloads. A clean canary check over TLS proves destinations only, unless TLS was
  terminated in a test proxy.
- MUST say which code paths the run did not exercise.

## Stop and ask

- The job needs real credentials to run. Use test credentials or ask.
- An unexpected host appears that is a known analytics or tracking service. Ask the owner whether that is allowed.

## Next

`tk-review-security` (findings) · `tk-review` (verdict). At scale, an organisation's packet-capture platform can
answer the same question by the job's address and time window.
