"""L1 verification of `read` for non-paper sources: github/web branches, identity, skeleton."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paperwiki


class ReadSourceTests(unittest.TestCase):
    def _args(self, root, target, slug=None):
        return type("A", (), {"paper": target, "root": str(root), "report_slug": slug})

    def test_read_github_repo_creates_source_record(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                self.assertEqual(url, "https://raw.githubusercontent.com/microsoft/TaskWeaver/HEAD/README.md")
                return "# TaskWeaver\n\nA code-first agent framework."

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(root, "https://github.com/microsoft/TaskWeaver", "taskweaver"))

            record = json.loads((root / "reports/taskweaver/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "source")
            self.assertEqual(record["source_type"], "github")
            self.assertEqual(record["title"], "microsoft/TaskWeaver")
            self.assertTrue(record["paper_id"].startswith("url:"))
            report = (root / "reports/taskweaver/report.md").read_text(encoding="utf-8")
            self.assertIn("read-source", report)
            self.assertNotIn("paper-analyzer", report)

    def test_read_blog_url_creates_source_record_with_page_title(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                return "<html><head><title>Effective Context  Engineering</title></head><body>x</body></html>"

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(
                    root, "https://www.anthropic.com/engineering/effective-context-engineering", "ece"))

            record = json.loads((root / "reports/ece/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["source_type"], "blog")
            self.assertEqual(record["title"], "Effective Context Engineering")
            self.assertEqual(record["paper_id"],
                             paperwiki.url_source_id("https://www.anthropic.com/engineering/effective-context-engineering"))

    def test_non_arxiv_url_with_digit_pattern_is_not_misread_as_arxiv(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                self.assertNotIn("export.arxiv.org", url)
                return "<html><head><title>Post 2024.12345</title></head><body>x</body></html>"

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(root, "https://blog.example.com/2024.12345-post", "post"))

            record = json.loads((root / "reports/post/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "source")

    def test_arxiv_doi_uses_arxiv_api_instead_of_crossref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            atom = """<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>Paper</title><summary>A</summary><published>2024-01-01</published><author><name>A</name></author></entry></feed>"""

            def fake_fetch(url, binary=False):
                self.assertNotIn("api.crossref.org", url)
                return b"%PDF" if binary else atom

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(root, "https://doi.org/10.48550/arXiv.2401.12345", "paper"))

            record = json.loads((root / "reports/paper/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["paper_id"], "arxiv:2401.12345")

    def test_paper_record_has_no_source_kind(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdf = root / "Local Paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            paperwiki.cmd_read(self._args(root, str(pdf)))
            record = json.loads((root / "reports/local-paper/record.json").read_text(encoding="utf-8"))
            self.assertNotIn("kind", record)


if __name__ == "__main__":
    unittest.main()
