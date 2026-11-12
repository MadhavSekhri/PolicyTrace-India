import tempfile
import unittest
from pathlib import Path
from policytrace.store import connect, ingest, history, diff_versions, search

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

    def test_reject_diff_between_different_sources(self):
        a = self.record("one")
        b = ingest(self.db, source_url="https://example.com/other",
                   publisher="A", title="B", body="two")
        with self.assertRaises(ValueError):
            diff_versions(self.db, a["id"], b["id"])


if __name__ == "__main__":
    unittest.main()
