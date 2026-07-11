import tempfile
import unittest
from pathlib import Path
import paperwiki


class PaperWikiTests(unittest.TestCase):
    def test_identity_precedence(self):
        self.assertEqual(paperwiki.paper_id({"title":"X","doi":"10.1/ABC","arxiv_id":"1234.5678"}), "doi:10.1/abc")
        self.assertEqual(paperwiki.paper_id({"title":"X","arxiv_id":"1234.5678v2"}), "arxiv:1234.5678")

    def test_merge_duplicate_arxiv(self):
        rows=paperwiki.merge([
            {"title":"Test","arxiv_id":"1234.5678","provenance":[{"provider":"a"}]},
            {"title":"Test","arxiv_id":"1234.5678v2","venue":"X","provenance":[{"provider":"b"}]},
        ])
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["venue"],"X"); self.assertEqual(len(rows[0]["provenance"]),2)

    def test_deposit_is_idempotent_and_preserves_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); report=root/"report.md"; report.write_text("# Test Paper\n\nSummary",encoding="utf-8")
            args=type("A",(),{"input":str(report),"root":str(root)})
            paperwiki.cmd_deposit(args); target=next((root/"wiki/papers").glob("*.md"))
            target.write_text(target.read_text(encoding="utf-8").replace("## User notes\n\n","## User notes\n\nMy insight\n"),encoding="utf-8")
            paperwiki.cmd_deposit(args)
            self.assertEqual(len(list((root/"wiki/papers").glob("*.md"))),1)
            self.assertIn("My insight",target.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
