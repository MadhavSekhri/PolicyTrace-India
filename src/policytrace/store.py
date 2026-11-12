"""SQLite-backed source-aware revision history."""
import difflib
import hashlib
import sqlite3
from urllib.parse import urlsplit
from datetime import datetime, timezone

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_SOURCE_URL_CHARS = 2048
MAX_SEARCH_CHARS = 512
MAX_SEARCH_RESULTS = 100



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


def _valid_source_url(source_url):
    if not isinstance(source_url, str) or not 0 < len(source_url) <= MAX_SOURCE_URL_CHARS:
        return False
    if any(ord(char) <= 32 or ord(char) == 127 for char in source_url):
        return False
    if "\\" in source_url:
        return False
    try:
        parts = urlsplit(source_url)
        port = parts.port  # Raises ValueError for malformed or out-of-range ports.
        return (
            parts.scheme in ("https", "http")
            and bool(parts.hostname)
            and parts.username is None
            and parts.password is None
            and "@" not in parts.netloc
            and port != 0
        )
    except ValueError:
        return False


def ingest(db, *, source_url, publisher, title, body, observed_at=None):
    if not _valid_source_url(source_url):
        raise ValueError("source_url must be a bounded absolute HTTP(S) URL without credentials or whitespace")
    for name, value, maximum in (("publisher", publisher, 256), ("title", title, 512)):
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > maximum
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError(f"{name} must be nonempty single-line text within {maximum} characters")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("body must be nonempty Unicode text")
    if len(body) > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds 2 MiB limit")
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("body must contain valid UTF-8 text") from exc
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise ValueError("document exceeds 2 MiB UTF-8 byte limit")
    digest = hashlib.sha256(encoded).hexdigest()
    if observed_at is not None:
        if not isinstance(observed_at, str):
            raise ValueError("observed_at must be ISO-8601 timezone-aware text")
        try:
            parsed = datetime.fromisoformat(observed_at)
        except ValueError as exc:
            raise ValueError("observed_at must be valid ISO-8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("observed_at needs an explicit timezone")
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
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_SEARCH_CHARS:
        raise ValueError("query must be nonempty text of at most 512 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_SEARCH_RESULTS:
        raise ValueError("limit must be an integer between 1 and 100")
    # Use a single ASCII punctuation escape character instead of interpolating SQL.
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
