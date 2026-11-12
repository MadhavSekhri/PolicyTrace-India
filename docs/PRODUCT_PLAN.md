# PolicyTrace India — Product & Engineering RFC

## Mission and reviewer test
An evidence-first, offline-first platform for tracking changes to official public policy documents: precisely what text changed, when it was observed, where it came from, and what is actually verified. Reviewer demo: ingest two *fictional* policy notices, compare changes, export an auditable record; nothing is presented as a verified government announcement.

## Market and differentiation
Audience: civic researchers, journalists, compliance teams, policy analysts, and data engineering teams. Alternatives are bookmarks, screenshots, search, generalized web monitors, and spreadsheets. Unique angle: traceability to original document URLs, immutable logical revisions, structured provenance, deterministic diffs and portable evidence bundles — not another news headline scraper.

## Product requirements
1. Full provenance model: Source (canonical ID, publisher, territory, legal URL, permitted retrieval method), Capture (observed timestamp, MIME, byte checksum, response metadata), Revision (content digest, optional publication date and exact text). Never conflate published and observed dates.
2. Offline-first ingest of user-provided files with bounded bytes and strict Unicode validation. Network retrieval must be explicitly opted in and per-source permission reviewed.
3. Idempotent versioning, document-level diff, search and machine-readable JSONL export with pagination and stable IDs.
4. Schema migrations, restore/backup strategy, consistent error codes and atomic operations.
5. Tests with synthetic fixtures, never fabricated real policy sources; disclose parsing uncertainty.

## Architecture and trust boundaries
CLI/file adapter -> strict URL/metadata/input validator -> content digest -> versioned SQLite transaction -> query/diff/export interface. Future source connectors form a separate boundary; HTTP access must defend against SSRF, redirects, DNS rebinding, private addresses, excessive transfer sizes and prohibited crawling. An LLM summary, if eventually provided, must cite exact retrieved spans and clearly identify interpretations.

## Out of scope
Legal certification of a government document, investment advice, stealth crawling, unlimited scraping, secret collection, real-time prediction, unaudited policy summaries. SHA256 alone does not prevent a privileged actor from modifying both text and digest.

## Execution gates
**P0 (initial PR):** harden absolute source URL parsing (reject spaces, userinfo and ambiguous hosts), cap document size and query size, add malicious-input/boundary tests; keep public API backward compatible for valid inputs.
**P1:** normalized Source/Capture/Revision tables with migrations, JSONL export, indexed full-text search, read-only API contract.
**P2:** authorized connectors, per-source attribution and legal checks, integrity manifests, source-level tests and retry/backoff.
**P3:** read-only web UI with timeline comparisons, user-controlled scheduled checks, optional citation-grounded explanation.

## Quality and evaluation
TDD for edge cases, Python 3.10/3.12 CI, type checking and linting, dependency review, performance benchmark on thousands of revisions, repairable migrations, semver, example integrations, reproducible releases and package distribution. User-success target: a new developer can get the same revision diff in <10 minutes without credentials.

## Security and privacy
No network by default, never follow source URLs in basic CLI, no sensitive text in logs by default, file ingestion size checks, SQL parameterization and wildcard escaping, protected backup/export workflow. Use threat model in docs/THREAT_MODEL.md.

## Adoption proof
Meaningful external dependents, reproducible demonstrations with authentic citations and permissions, externally raised bugs and PRs, public documentation and release artifacts. Do not manufacture metrics or claim funding eligibility from repository creation.

## Collaboration
Propose scoped features and provide tests/fixtures in review. Optional integrations: Agent Audit Kit checks source-citation pipelines; OTel Agent Observer records only safe ingestion metadata; OSS Readiness checks project hygiene. Keep all packages independently installable.
