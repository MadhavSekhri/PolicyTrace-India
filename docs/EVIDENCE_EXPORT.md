# P1: Portable, versioned evidence export (JSONL)

Use policytrace export --db policy.sqlite3 --limit 100 > evidence.jsonl.
Use --include-text to deliberately include potentially sensitive imported document bodies.
Use --after-id N for exclusive stable ID-cursor pagination and --source-url to filter.
At most 1,000 rows are emitted per batch; export does not connect to the network.

Each JSON record has schema_version 1; kind policytrace.revision; locally assigned
revision_id; user-provided source_url, publisher and title; observed_at; sha256
of UTF-8 text; text_included; and provenance_verified (always false).
The text field is present only when --include-text was requested.

The generator recomputes body hashes before emitting records and refuses
tampered local records. Consumers may call policytrace.evidence.verify_record
to check exported bodies when explicitly included. A metadata-only export
cannot independently verify its content digest.

SHA-256 matching is not a government signature, document authenticity
certificate or tamper-proof ledger. Source URLs and attribution are user claims.
Local revision IDs are not globally unique. JSONL containing text should
not be published without checking confidentiality and redistribution rights.
