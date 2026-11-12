"""SQLite-backed source-aware revision history."""
import difflib
import hashlib
import sqlite3
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
    if not source_url.startswith(("https://", "http://")):
        raise ValueError("source_url must be an HTTP(S) URL")
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
    if not query.strip():
        raise ValueError("query must not be empty")
    needle = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    rows = db.execute(
        """SELECT id,source_url,publisher,title,observed_at FROM documents
           WHERE body LIKE ? ESCAPE '\' OR title LIKE ? ESCAPE '\'
           ORDER BY id DESC LIMIT ?""",
        (f"%{needle}%", f"%{needle}%", limit),
    ).fetchall()
    return [dict(row) for row in rows]
