# PolicyTrace India — Threat Model

Assets: attributed policy records, local SQLite state, user filesystem, future trusted connector settings.
Untrusted inputs: source URLs, publisher/title, text bytes and potential future HTTP responses.
Trust boundaries: caller -> validator -> storage -> CLI output; future downloader -> parser.

| Threat | Risk | Control |
|---|---|---|
| URL confusion | userinfo, whitespace, malformed ports and hosts appear trustworthy | strict urlsplit validation, tests for host, percent escapes, whitespace and userinfo |
| SSRF (future) | cloud metadata / private network reachable from server | no HTTP fetching currently; allowlist and IP/redirect verification before adding connector |
| Resource exhaustion | huge text or search strings consume disk/time | explicit input budgets, bounded query size, error tests |
| SQL/wildcard injection | query expands unintended results | bound parameters and escaped LIKE wildcards |
| False provenance | unverified statement treated as official source | source URL is *claimed*, not authenticated; signed manifests later |
| Content tampering | attacker rewrites body and digest | checksums detect accidental mismatches only; backups, signed evidence in future |
| Metadata mismatch | publisher/date changes without revision event | future explicit source and capture identity fields |
| Privacy / licensing | records redistributed unlawfully | no automatic network or redistribution; per-source permissions and clear provenance |

Security exit criteria: add tests for invalid URL cases and max bytes; no unrequested network calls, opaque error codes, and explicit statement of unverifiable source authenticity.
