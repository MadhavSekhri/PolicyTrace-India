# PolicyTrace India

Track source-attributed policy document revisions in a local SQLite store.

**Status:** early open-source prototype. This program does not crawl government websites, verify government claims, or provide investment advice. All example notices are fictional.

## Install

Requires Python 3.10 or later.

    python -m pip install -e .

## Try it

    policytrace ingest --db policy.sqlite3 --source-url https://example.gov.in/notice/123 --publisher "Example Public Agency" --title "Sample notice" --file examples/notice_v1.txt
    policytrace history --db policy.sqlite3 --source-url https://example.gov.in/notice/123
    policytrace search --db policy.sqlite3 --query funding
    policytrace latest --db policy.sqlite3
    policytrace verify --db policy.sqlite3

You can ingest a new version of the same source and compare revision IDs:

    policytrace ingest --db policy.sqlite3 --source-url https://example.gov.in/notice/123 --publisher "Example Public Agency" --title "Sample notice" --file examples/notice_v2.txt
    policytrace diff 1 2 --db policy.sqlite3

Each revision stores the source URL, publisher, title, observation timestamp, SHA-256 digest, and document text. Reingesting unchanged text is idempotent. `latest` returns the most recent observed revision per URL without returning full document bodies; `verify` compares stored text against stored SHA-256 digests and exits with code 1 if mismatched. **Checksums detect accidental changes but do not prove government provenance or prevent a malicious database rewrite.**

## Portable evidence export (P1)

Export a paginated, versioned stream suitable for independent tools:

    policytrace export --db policy.sqlite3 --limit 100 > evidence.jsonl
    policytrace export --db policy.sqlite3 --after-id 100 --include-text > with-text.jsonl

Text is excluded by default; --include-text explicitly opts in. The exporter
checks source-row digests, labels provenance as unverified and never fetches
government URLs. See [evidence export format](docs/EVIDENCE_EXPORT.md).

Try the [public-source pilot](docs/PUBLIC_SOURCE_PILOT.md) with two government releases on India's National Critical Mineral Mission.

## Input and provenance safety

The default CLI is strictly offline and never downloads the `--source-url`; that field is a claimed provenance identifier, not an authenticated government citation. Documents must be valid UTF-8 and at most **2 MiB**; source URLs must be absolute HTTP(S) URLs without embedded spaces, control characters, or userinfo. Publisher and title are bounded single-line values. Search is limited to 512-character queries and at most 100 results per call. Observation timestamps and publication timestamps are different concepts; the current revision store tracks observation only.

For the detailed architecture, remaining risks and planned connector work, see [Product plan](docs/PRODUCT_PLAN.md) and [Threat model](docs/THREAT_MODEL.md).

## Test

    python -m unittest discover -s tests -v

## Contributions

See CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md. Please provide sourced, reproducible examples and respect third-party websites, terms and privacy.

## License

MIT (see LICENSE).

## Architecture and security

This is an actively developed prototype, not a certification or completed production service. Review the [product design and acceptance gates](docs/PRODUCT_PLAN.md), [threat model](docs/THREAT_MODEL.md) before depending on it. Changes are proposed through draft pull requests with automated tests and security-focused code review.
