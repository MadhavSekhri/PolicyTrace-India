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

You can ingest a new version of the same source and compare revision IDs:

    policytrace ingest --db policy.sqlite3 --source-url https://example.gov.in/notice/123 --publisher "Example Public Agency" --title "Sample notice" --file examples/notice_v2.txt
    policytrace diff 1 2 --db policy.sqlite3

Each revision stores the source URL, publisher, title, observation timestamp, SHA-256 digest, and document text. Reingesting unchanged text is idempotent.

## Test

    python -m unittest discover -s tests -v

## Contributions

See CONTRIBUTING.md, SECURITY.md and CODE_OF_CONDUCT.md. Please provide sourced, reproducible examples and respect third-party websites, terms and privacy.

## License

MIT (see LICENSE).
