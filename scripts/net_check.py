#!/usr/bin/env python3
"""Network allowlist check: did the code under test talk only to the hosts it is allowed to?

WHAT:       Compares observed outbound connections (from a packet capture or connection log) with an allowlist of
            hosts, wildcard domains, CIDR ranges and ports; reports unexpected destinations and ports; reports a
            BLOCKER when a planted canary secret appears in captured payload text.
WHY:        "The code does not phone home / leak secrets" must be shown from traffic, not argued from reading code.
RUNS WHEN:  tk-verify-network, after a sandboxed run with capture:
            `tshark -r run.pcap -T fields -e ip.dst -e tcp.dstport -e tls.handshake.extensions_server_name`
            → `python scripts/net_check.py --fields fields.tsv --allow allow.json [--payload strings.txt --canary X]`
AFFECTS:    Prints findings JSON; exit 1 when any finding. Reads only.
CAUTION:    Encrypted payloads hide canaries unless the canary is checked at a decrypting proxy or in plaintext
            protocols; a clean result for TLS traffic proves destinations, not contents. Never echoes the canary.
CHANGED:    2026-11-20 · v0.1 · new
"""
from __future__ import annotations

import argparse
import fnmatch
import ipaddress
import json
import sys
from typing import Any, Dict, List, Optional


def _host_allowed(dst: str, hosts: List[str]) -> bool:
    try:
        ip = ipaddress.ip_address(dst)
    except ValueError:
        ip = None
    for pat in hosts:
        if "/" in pat and ip is not None:
            try:
                if ip in ipaddress.ip_network(pat, strict=False):
                    return True
            except ValueError:
                continue
        elif pat.startswith("*."):
            if dst.endswith(pat[1:]) and dst.count(".") >= pat.count("."):
                return True
        elif fnmatch.fnmatchcase(dst, pat):
            return True
    return False


def check(conns: List[Dict[str, Any]], allow: Dict[str, Any], payload_text: str = "",
          canary: Optional[str] = None) -> List[Dict[str, Any]]:
    """WHAT: conns [{dst, port}] vs allow {hosts:[...], ports:[...]} (+ canary in payload) → findings."""
    hosts, ports = list(allow.get("hosts") or []), set(int(p) for p in allow.get("ports") or [])
    out: List[Dict[str, Any]] = []
    seen = set()
    for c in conns:
        dst, port = str(c.get("dst")), int(c.get("port") or 0)
        key = (dst, port)
        if key in seen:
            continue
        seen.add(key)
        if not _host_allowed(dst, hosts):
            out.append({"rule": "unexpected_host", "category": "security", "severity": "MAJOR", "file": "<network>",
                        "line": 0, "why": f"Connection to {dst}:{port}, which is not on the allowlist.",
                        "evidence": f"{dst}:{port}", "confidence": 4,
                        "fix": "Remove the call, or add the host to the allowlist with a reason.", "encode": None})
        elif ports and port not in ports:
            out.append({"rule": "unexpected_port", "category": "security", "severity": "MAJOR", "file": "<network>",
                        "line": 0, "why": f"Allowed host {dst} reached on unexpected port {port}.",
                        "evidence": f"{dst}:{port}", "confidence": 4,
                        "fix": "Use the expected port or explain the new one.", "encode": None})
    if canary and canary in payload_text:
        out.append({"rule": "canary_leak", "category": "security", "severity": "BLOCKER", "file": "<network>",
                    "line": 0, "why": "The planted canary secret left the sandbox in network traffic.",
                    "evidence": "canary found in captured payload (value withheld)", "confidence": 5,
                    "fix": "Find the code path that sends secrets or environment values out; remove it.",
                    "encode": "egress allowlist enforced by the sandbox network"})
    return out


def parse_tshark(text: str) -> List[Dict[str, Any]]:
    """WHAT: tshark fields (ip.dst, port, optional TLS SNI or DNS name) → [{dst, port}]; prefers the name over the IP."""
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[1].strip().isdigit():
            continue
        name = parts[2].strip() if len(parts) > 2 else ""
        out.append({"dst": name or parts[0].strip(), "port": int(parts[1])})
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen network allowlist check")
    ap.add_argument("--fields", required=True, help="tshark fields output (ip.dst, port, [server name])")
    ap.add_argument("--allow", required=True, help='JSON: {"hosts": [...], "ports": [...]}')
    ap.add_argument("--payload", help="text dump of captured payloads (e.g. tshark -x or strings)")
    ap.add_argument("--canary", help="canary value planted in the run's environment")
    a = ap.parse_args(argv)
    conns = parse_tshark(open(a.fields, encoding="utf-8").read())
    payload = open(a.payload, encoding="utf-8", errors="replace").read() if a.payload else ""
    findings = check(conns, json.load(open(a.allow, encoding="utf-8")), payload, a.canary)
    print(json.dumps({"connections": len(conns), "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
