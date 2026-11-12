import tempfile
import unittest
from pathlib import Path
from policytrace.store import connect, ingest, history, diff_versions, search, latest, verify_integrity

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

    def test_reject_diff_between_different_sources(self):
        a = self.record("one")
        b = ingest(self.db, source_url="https://example.com/other",
                   publisher="A", title="B", body="two")
        with self.assertRaises(ValueError):
            diff_versions(self.db, a["id"], b["id"])


if __name__ == "__main__":
    unittest.main()
