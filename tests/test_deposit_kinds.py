"""L1 verification of deposit for kind: source and kind: topic records."""
import json
import tempfile
import unittest
from pathlib import Path

import paperwiki


def _seed_source_report(root):
    folder = root / "reports/ece"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text("---\npaper_id: url:abcdef123456\n---\n\n# Effective Context Engineering\n\nBody\n",
                      encoding="utf-8")
    record = {"paper_id": "url:abcdef123456", "title": "Effective Context Engineering",
              "kind": "source", "source_type": "blog",
              "source_url": "https://www.anthropic.com/engineering/x",
              "reading": {"concepts": ["Context Rot"], "methods": ["Compaction"],
                          "datasets": [], "topics": ["Context Engineering"], "tools": ["LLMLingua"]}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    return report


class DepositSourceTests(unittest.TestCase):
    def test_source_record_lands_in_wiki_sources_with_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            self.assertEqual(list((root / "wiki").glob("papers/*.md")), [])
            page = next((root / "wiki/sources").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("source_type: blog", page)
            self.assertIn("url: https://www.anthropic.com/engineering/x", page)
            self.assertIn("[[reports/ece/report|Effective Context Engineering report]]", page)

    def test_source_deposit_links_tools_collection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            tool = (root / "wiki/tools/llmlingua.md").read_text(encoding="utf-8")
            self.assertIn("type: tool", tool)
            self.assertIn("Effective Context Engineering", tool)

    def test_source_deposit_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)
            args = type("A", (), {"input": str(report), "root": str(root)})
            paperwiki.cmd_deposit(args)
            paperwiki.cmd_deposit(args)
            self.assertEqual(len(list((root / "wiki/sources").glob("*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
