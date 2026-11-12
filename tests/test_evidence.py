"""Evidence export must be paginated, privacy-safe and integrity checked."""
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from policytrace.cli import main
from policytrace.evidence import iter_evidence, verify_record, write_jsonl
from policytrace.store import connect, ingest

URL = "https://example.gov.in/fictional/notice"


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name) / "evidence.db"
        self.db = connect(self.dbpath)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def record(self, body, url=URL):
        return ingest(self.db, source_url=url, publisher="Fictional Office",
                      title="Fictional notice", body=body)["id"]

    def test_default_excludes_document_text(self):
        self.record("Confidential local demonstration text")
        record = next(iter_evidence(self.db))
        self.assertEqual(record["schema_version"], 1)
        self.assertFalse(record["text_included"])
        self.assertFalse(record["provenance_verified"])
        self.assertNotIn("text", record)

    def test_paginate_and_filter_by_source(self):
        a = self.record("one")
        b = self.record("two", url="https://example.gov.in/fictional/other")
        c = self.record("three")
        self.assertEqual(next(iter_evidence(self.db, limit=1))["revision_id"], a)
        self.assertEqual([r["revision_id"] for r in iter_evidence(self.db, after_id=a)], [b, c])
        self.assertEqual([r["revision_id"] for r in iter_evidence(self.db, source_url=URL)], [a, c])

    def test_opt_in_body_and_verify(self):
        self.record("नमूना पाठ\nPublic sample.")
        out = StringIO()
        self.assertEqual(write_jsonl(self.db, out, include_text=True), 1)
        record = json.loads(out.getvalue())
        self.assertTrue(verify_record(record))
        self.assertEqual(record["sha256"], hashlib.sha256(record["text"].encode()).hexdigest())
        record["text"] = "tampered"
        self.assertFalse(verify_record(record))

    def test_corrupt_database_fails_closed(self):
        ident = self.record("original")
        with self.db:
            self.db.execute("UPDATE documents SET body='tampered' WHERE id=?", (ident,))
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            list(iter_evidence(self.db))

    def test_limits_and_unverifiable_no_text(self):
        self.record("one")
        for args in ({"limit": 0}, {"limit": 1001}, {"limit": True},
                     {"after_id": -1}, {"after_id": False}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                list(iter_evidence(self.db, **args))
        with self.assertRaisesRegex(ValueError, "without included text"):
            verify_record(next(iter_evidence(self.db)))

    def test_cli_output_is_jsonl(self):
        self.record("synthetic sample")
        with redirect_stdout(StringIO()) as stream:
            status = main(["export", "--db", str(self.dbpath), "--include-text"])
        self.assertEqual(status, 0)
        lines = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(verify_record(lines[0]))


if __name__ == "__main__":
    unittest.main()
