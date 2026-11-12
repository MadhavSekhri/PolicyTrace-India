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

## Test

    python -m unittest discover -s tests -v

## Contributions

See CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md. Please provide sourced, reproducible examples and respect third-party websites, terms and privacy.

## License

MIT (see LICENSE).
