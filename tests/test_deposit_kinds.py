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


def _seed_topic_report(root, with_list=False):
    folder = root / "reports/topic-context-compaction"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text("---\ntopic_id: context-compaction\nkind: topic\n---\n\n# 上下文压缩综述\n\n正文\n",
                      encoding="utf-8")
    record = {"kind": "topic", "topic_slug": "context-compaction", "title": "Context Compaction",
              "list_slug": "hx" if with_list else None,
              "sources": [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                           "url": "https://platform.claude.com/docs/compaction",
                           "source_type": "docs", "role": "core", "status": "studied"}],
              "entities": {"concepts": ["Context Rot"], "methods": ["Progressive Compaction"],
                           "tools": ["LLMLingua"]},
              "created": "T0", "updated": "T0"}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    if with_list:
        lp = root / "reading-lists/hx.json"
        lp.parent.mkdir(parents=True)
        lp.write_text(json.dumps({"list_slug": "hx", "source_repo": "r", "retrieved_at": "T0",
                                  "entries": [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                                               "url": "https://platform.claude.com/docs/compaction",
                                               "source_type": "docs", "section_path": ["S"],
                                               "description": "", "status": "studied",
                                               "added_at": "T0", "status_updated_at": "T0"}]}),
                      encoding="utf-8")
    return report


class DepositTopicTests(unittest.TestCase):
    def test_topic_record_builds_english_graph_page(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            page = (root / "wiki/topics/context-compaction.md").read_text(encoding="utf-8")
            self.assertIn("type: topic", page)
            self.assertIn("[[reports/topic-context-compaction/report|Context Compaction 综述]]", page)
            self.assertIn("[[progressive-compaction|Progressive Compaction]]", page)
            self.assertIn("[[llmlingua|LLMLingua]]", page)
            self.assertIn("[[compaction-docs|Compaction Docs]]", page)
            source_page = (root / "wiki/sources/compaction-docs.md").read_text(encoding="utf-8")
            self.assertIn("url: https://platform.claude.com/docs/compaction", source_page)
            self.assertIn("source_id: url:aaa111222333", source_page)
            self.assertIn("Context Compaction", source_page)
            self.assertIn("Context Compaction", (root / "index.md").read_text(encoding="utf-8"))
            self.assertIn("deposit topic:context-compaction", (root / "log.md").read_text(encoding="utf-8"))

    def test_topic_deposit_preserves_existing_related_papers_and_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)
            topics = root / "wiki/topics"
            topics.mkdir(parents=True)
            (topics / "context-compaction.md").write_text(
                "---\ntitle: \"Context Compaction\"\ntype: topic\n---\n\n# Context Compaction\n\n"
                "## Related papers\n\n- [[arxiv-1234-5678|Old Paper]]\n\n## User notes\n\nkeep me\n",
                encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            page = (topics / "context-compaction.md").read_text(encoding="utf-8")
            self.assertIn("[[arxiv-1234-5678|Old Paper]]", page)
            self.assertIn("keep me", page)

    def test_topic_deposit_marks_list_entries_deposited(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root, with_list=True)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            entry = json.loads((root / "reading-lists/hx.json").read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "deposited")

    def test_topic_deposit_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)
            args = type("A", (), {"input": str(report), "root": str(root)})
            paperwiki.cmd_deposit(args)
            paperwiki.cmd_deposit(args)
            page = (root / "wiki/topics/context-compaction.md").read_text(encoding="utf-8")
            self.assertEqual(page.count("[[llmlingua|LLMLingua]]"), 1)
            self.assertEqual(len(list((root / "wiki/sources").glob("*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
