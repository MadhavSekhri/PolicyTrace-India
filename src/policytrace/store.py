"""SQLite-backed source-aware revision history."""
import difflib
import hashlib
import sqlite3
from urllib.parse import urlsplit
from datetime import datetime, timezone


def connect(path):
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_url TEXT NOT NULL,
        publisher TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        UNIQUE(source_url, sha256)
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS documents_by_source ON documents(source_url, id)")
    db.commit()
    return db


def ingest(db, *, source_url, publisher, title, body, observed_at=None):
    for name, value in (("source_url", source_url), ("publisher", publisher),
                        ("title", title), ("body", body)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be nonempty")
    try:
        parts = urlsplit(source_url)
        valid_url = parts.scheme in ("https", "http") and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        valid_url = False
    if not valid_url:
        raise ValueError("source_url must be an absolute HTTP(S) URL with host")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    existing = db.execute(
        "SELECT id FROM documents WHERE source_url=? AND sha256=?",
        (source_url, digest),
    ).fetchone()
    if existing:
        return {"status": "unchanged", "id": existing["id"], "sha256": digest}
    timestamp = observed_at or datetime.now(timezone.utc).isoformat()
    with db:
        cursor = db.execute(
            """INSERT INTO documents (source_url,publisher,title,body,sha256,observed_at)
               VALUES (?,?,?,?,?,?)""",
            (source_url, publisher, title, body, digest, timestamp),
        )
    return {"status": "new_revision", "id": cursor.lastrowid, "sha256": digest}


def history(db, source_url):
    rows = db.execute(
        """SELECT id,source_url,publisher,title,sha256,observed_at FROM documents
           WHERE source_url=? ORDER BY id""",
        (source_url,),
    ).fetchall()
    return [dict(row) for row in rows]


def diff_versions(db, old_id, new_id):
    old = db.execute("SELECT * FROM documents WHERE id=?", (old_id,)).fetchone()
    new = db.execute("SELECT * FROM documents WHERE id=?", (new_id,)).fetchone()
    if not old or not new:
        raise ValueError("both revision IDs must exist")
    if old["source_url"] != new["source_url"]:
        raise ValueError("revisions must belong to the same source")
    return "".join(difflib.unified_diff(
        old["body"].splitlines(keepends=True),
        new["body"].splitlines(keepends=True),
        fromfile=f"revision-{old_id}",
        tofile=f"revision-{new_id}",
    ))


def search(db, query, limit=25):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must not be empty")
    # Escape LIKE wildcards using ! as an explicit single-character escape.
    needle = query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    rows = db.execute(
        """SELECT id,source_url,publisher,title,observed_at FROM documents
           WHERE body LIKE ? ESCAPE '!' OR title LIKE ? ESCAPE '!'
           ORDER BY id DESC LIMIT ?""",
        (f"%{needle}%", f"%{needle}%", limit),
    ).fetchall()
    return [dict(row) for row in rows]


def latest(db, source_url=None):
    """Return latest revision metadata, once per tracked source."""
    if source_url is not None:
        records = db.execute(
            """SELECT id,source_url,publisher,title,sha256,observed_at
               FROM documents WHERE source_url=? ORDER BY id DESC LIMIT 1""",
            (source_url,),
        ).fetchall()
    else:
        records = db.execute(
            """SELECT id,source_url,publisher,title,sha256,observed_at FROM documents d
               WHERE id=(SELECT MAX(id) FROM documents WHERE source_url=d.source_url)
               ORDER BY id DESC""",
        ).fetchall()
    return [dict(record) for record in records]


def verify_integrity(db, source_url=None):
    """Check stored document text against its recorded SHA-256 checksum.

    This detects accidental corruption or edits to stored text; it does not
    authenticate publisher provenance or guarantee tamper-proof storage.
    """
    if source_url is None:
        records = db.execute("SELECT id,body,sha256 FROM documents").fetchall()
    else:
        records = db.execute(
            "SELECT id,body,sha256 FROM documents WHERE source_url=?", (source_url,)
        ).fetchall()
    mismatches = [
        row["id"] for row in records
        if hashlib.sha256(row["body"].encode("utf-8")).hexdigest() != row["sha256"]
    ]
    return {
        "checked": len(records),
        "ok": not mismatches,
        "mismatch_ids": mismatches,
        "caveat": "Checksum matching does not prove source authenticity.",
    }
