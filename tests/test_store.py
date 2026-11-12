import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from policytrace.store import (
    MAX_DOCUMENT_BYTES, connect, ingest, history, diff_versions,
    search, latest, verify_integrity,
)
from policytrace.cli import main

URL = "https://example.gov.in/notice/123"


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "data.sqlite3")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def record(self, body):
        return ingest(self.db, source_url=URL, publisher="Example agency",
                      title="Test notice", body=body)

    def test_revisions_are_idempotent(self):
        first = self.record("one\n")
        second = self.record("one\n")
        third = self.record("two\n")
        self.assertEqual(first["status"], "new_revision")
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(len(history(self.db, URL)), 2)
        self.assertIn("+two", diff_versions(self.db, first["id"], third["id"]))
        self.assertEqual(len(search(self.db, "two")), 1)

    def test_reject_invalid_source(self):
        with self.assertRaises(ValueError):
            ingest(self.db, source_url="javascript:alert(1)",
                   publisher="A", title="B", body="C")

    def test_verify_detects_modified_body(self):
        record = self.record("original")
        self.assertTrue(verify_integrity(self.db)["ok"])
        with self.db:
            self.db.execute("UPDATE documents SET body=? WHERE id=?",
                            ("altered", record["id"]))
        result = verify_integrity(self.db)
        self.assertFalse(result["ok"])
        self.assertEqual(result["mismatch_ids"], [record["id"]])

    def test_latest_is_per_source(self):
        self.record("first")
        current = self.record("second")
        ingest(self.db, source_url="https://example.gov.in/other",
               publisher="Example agency", title="Other notice", body="third")
        items = latest(self.db)
        self.assertEqual(len(items), 2)
        self.assertEqual(latest(self.db, URL)[0]["id"], current["id"])

    def test_search_escapes_sql_wildcards(self):
        self.record("100% allocated")
        self.record("100 percent allocated")
        self.assertEqual(len(search(self.db, "%")), 1)
        self.assertEqual(len(search(self.db, "_")), 0)

    def test_host_required(self):
        with self.assertRaises(ValueError):
            ingest(self.db, source_url="https://", publisher="A", title="B", body="C")

    def test_reject_url_confusion_and_unsafe_characters(self):
        invalid = [
            "https://", "https://example.com:99999/path",
            "https://user:pass@example.com/policy", "https://@example.com/",
            "https://example.com/path\nother", "https://example.com/with space",
            "https://example.com\\@evil.test", "ftp://example.com/file",
            "https://example.com:0",
        ]
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                ingest(self.db, source_url=url, publisher="Agency", title="Notice", body="text")

    def test_body_and_search_budgets(self):
        with self.assertRaisesRegex(ValueError, "2 MiB"):
            self.record("z" * (MAX_DOCUMENT_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            self.record("\ud800")
        with self.assertRaises(ValueError):
            search(self.db, "x" * 513)
        for limit in (0, -1, 101, True, 0.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                search(self.db, "ok", limit)

    def test_bad_observation_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            ingest(self.db, source_url=URL, publisher="A", title="Notice",
                   body="text", observed_at="2026-11-12T14:00:00")

    def test_cli_refuses_oversized_document(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "large.txt"
            file.write_bytes(b"x" * (MAX_DOCUMENT_BYTES + 1))
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as err:
                    main(["ingest", "--source-url", URL, "--publisher", "A",
                          "--title", "Notice", "--file", str(file),
                          "--db", str(Path(folder) / "test.sqlite")])
            self.assertEqual(err.exception.code, 2)

    def test_reject_diff_between_different_sources(self):
        a = self.record("one")
        b = ingest(self.db, source_url="https://example.com/other",
                   publisher="A", title="B", body="two")
        with self.assertRaises(ValueError):
            diff_versions(self.db, a["id"], b["id"])


if __name__ == "__main__":
    unittest.main()
