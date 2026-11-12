"""Portable JSONL exports of locally observed, source-attributed revisions.

Source URLs are unverified claims; the database content digest is not a
publisher signature or guarantee against a fully compromised database.
"""
import hashlib
import json

SCHEMA_VERSION = 1
MAX_EXPORT_ROWS = 1000


def iter_evidence(db, *, source_url=None, after_id=0, limit=100, include_text=False):
    """Stream bounded revisions after the exclusive integer ID cursor."""
    if isinstance(after_id, bool) or not isinstance(after_id, int) or after_id < 0:
        raise ValueError("after_id must be a nonnegative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_EXPORT_ROWS:
        raise ValueError("limit must be an integer from 1 to 1000")
    if source_url is not None and not isinstance(source_url, str):
        raise ValueError("source_url filter must be text")
    if not isinstance(include_text, bool):
        raise ValueError("include_text must be a boolean")
    if source_url is None:
        cursor = db.execute(
            """SELECT id,source_url,publisher,title,body,sha256,observed_at
               FROM documents WHERE id>? ORDER BY id ASC LIMIT ?""",
            (after_id, limit))
    else:
        cursor = db.execute(
            """SELECT id,source_url,publisher,title,body,sha256,observed_at
               FROM documents WHERE id>? AND source_url=?
               ORDER BY id ASC LIMIT ?""",
            (after_id, source_url, limit))
    for row in cursor:
        digest = hashlib.sha256(row["body"].encode("utf-8")).hexdigest()
        if digest != row["sha256"]:
            raise ValueError("integrity mismatch for revision " + str(row["id"]))
        record = {
            "schema_version": SCHEMA_VERSION,
            "kind": "policytrace.revision",
            "revision_id": row["id"],
            "source_url": row["source_url"],
            "publisher": row["publisher"],
            "title": row["title"],
            "observed_at": row["observed_at"],
            "sha256": digest,
            "text_included": include_text,
            "provenance_verified": False,
        }
        if include_text:
            record["text"] = row["body"]
        yield record


def write_jsonl(db, output, **kwargs):
    """Stream one JSON record per line to a caller-owned writable file object."""
    count = 0
    for record in iter_evidence(db, **kwargs):
        output.write(json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n")
        count += 1
    return count


def verify_record(record):
    """Check a text-containing evidence record against its SHA-256 digest."""
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported evidence record schema")
    if record.get("kind") != "policytrace.revision":
        raise ValueError("unexpected evidence record kind")
    if record.get("text_included") is not True or not isinstance(record.get("text"), str):
        raise ValueError("cannot verify integrity without included text")
    expected = record.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("invalid SHA-256 digest")
    return hashlib.sha256(record["text"].encode("utf-8")).hexdigest() == expected
