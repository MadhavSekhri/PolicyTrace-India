"""Offline document-tracking CLI; does not crawl URLs."""
import argparse
import json
from pathlib import Path
from .store import connect, ingest, history, diff_versions, search


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
    for p in sub.choices.values():
        p.add_argument("--db", type=Path, default=Path("policytrace.sqlite3"))
    args = parser.parse_args(argv)
    db = connect(args.db)
    try:
        if args.command == "ingest":
            result = ingest(
                db, source_url=args.source_url, publisher=args.publisher,
                title=args.title, body=args.file.read_text(encoding="utf-8"))
        elif args.command == "history":
            result = history(db, args.source_url)
        elif args.command == "diff":
            result = {"diff": diff_versions(db, args.old, args.new)}
        else:
            result = search(db, args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
