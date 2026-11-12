"""Offline document-tracking CLI; does not crawl URLs."""
import argparse
import json
from pathlib import Path
from .store import (
    MAX_DOCUMENT_BYTES, connect, ingest, history, diff_versions,
    search, latest, verify_integrity,
)


def _read_document(path):
    if path.is_symlink():
        raise ValueError("document must not be a symbolic link")
    with path.open("rb") as stream:
        raw = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds 2 MiB limit")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("document must be UTF-8") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(prog="policytrace")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest")
    p.add_argument("--source-url", required=True)
    p.add_argument("--publisher", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--file", type=Path, required=True)
    p = sub.add_parser("history")
    p.add_argument("--source-url", required=True)
    p = sub.add_parser("diff")
    p.add_argument("old", type=int)
    p.add_argument("new", type=int)
    p = sub.add_parser("search")
    p.add_argument("--query", required=True)
    p = sub.add_parser("latest", help="Show latest revision per tracked source")
    p.add_argument("--source-url", default=None)
    p = sub.add_parser("verify", help="Check local body SHA-256 against recorded digests")
    p.add_argument("--source-url", default=None)
    for p in sub.choices.values():
        p.add_argument("--db", type=Path, default=Path("policytrace.sqlite3"))
    args = parser.parse_args(argv)
    db = connect(args.db)
    try:
        if args.command == "ingest":
            result = ingest(
                db, source_url=args.source_url, publisher=args.publisher,
                title=args.title, body=_read_document(args.file))
        elif args.command == "history":
            result = history(db, args.source_url)
        elif args.command == "diff":
            result = {"diff": diff_versions(db, args.old, args.new)}
        elif args.command == "search":
            result = search(db, args.query)
        elif args.command == "latest":
            result = latest(db, args.source_url)
        else:
            result = verify_integrity(db, args.source_url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == "verify" and not result["ok"] else 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
