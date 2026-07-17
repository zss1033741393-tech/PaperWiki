"""L1 verification of deposit for kind: source and kind: topic records."""
import json
import re
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

    def test_stub_then_deep_read_same_source_share_one_page(self):
        # A topic deposit stubs the source; a later deep-read deposit of the SAME source_id
        # must land on the same file and keep the stub's topic backlinks.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            topic_report = _seed_topic_report(root)
            paperwiki.cmd_deposit(type("A", (), {"input": str(topic_report), "root": str(root)}))

            folder = root / "reports/compaction-docs"
            folder.mkdir(parents=True)
            source_report = folder / "report.md"
            source_report.write_text("---\npaper_id: url:aaa111222333\n---\n\n# Compaction Docs\n\nDeep body\n",
                                     encoding="utf-8")
            record = {"paper_id": "url:aaa111222333", "title": "Compaction Docs", "kind": "source",
                      "source_type": "docs",
                      "source_url": "https://platform.claude.com/docs/compaction", "reading": {}}
            (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(source_report), "root": str(root)}))

            files = list((root / "wiki/sources").glob("*.md"))
            self.assertEqual([f.name for f in files], ["url-aaa111222333.md"])
            page = files[0].read_text(encoding="utf-8")
            self.assertIn("type: source", page)
            self.assertIn("source_id: url:aaa111222333", page)
            self.assertIn("Deep body", page)                                # deep-read body kept
            related = re.search(r"## Related pages\n\n(.*?)(?=\n## |\Z)", page, re.S)
            self.assertIsNotNone(related)
            self.assertIn("- [[context-compaction|Context Compaction]]", related.group(1))


def _seed_topic_report(root, with_list=False, with_blocked=False):
    folder = root / "reports/topic-context-compaction"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text("---\ntopic_id: context-compaction\nkind: topic\n---\n\n# 上下文压缩综述\n\n正文\n",
                      encoding="utf-8")
    sources = [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                "url": "https://platform.claude.com/docs/compaction",
                "source_type": "docs", "role": "core", "status": "studied"}]
    entries = [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                "url": "https://platform.claude.com/docs/compaction",
                "source_type": "docs", "section_path": ["S"],
                "description": "", "status": "studied",
                "added_at": "T0", "status_updated_at": "T0"}]
    if with_blocked:
        sources.append({"source_id": "url:bbb444555666", "title": "Paywalled Post",
                        "url": "https://blocked.example/post",
                        "source_type": "blog", "role": "core", "status": "blocked"})
        entries.append({"source_id": "url:bbb444555666", "title": "Paywalled Post",
                        "url": "https://blocked.example/post",
                        "source_type": "blog", "section_path": ["S"],
                        "description": "", "status": "blocked", "blocked_reason": "paywall",
                        "added_at": "T0", "status_updated_at": "T0"})
    record = {"kind": "topic", "topic_slug": "context-compaction", "title": "Context Compaction",
              "list_slug": "hx" if with_list else None,
              "sources": sources,
              "entities": {"concepts": ["Context Rot"], "methods": ["Progressive Compaction"],
                           "tools": ["LLMLingua"]},
              "created": "T0", "updated": "T0"}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    if with_list:
        lp = root / "reading-lists/hx.json"
        lp.parent.mkdir(parents=True)
        lp.write_text(json.dumps({"list_slug": "hx", "source_repo": "r", "retrieved_at": "T0",
                                  "entries": entries}),
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
            self.assertIn("[[url-aaa111222333|Compaction Docs]]", page)
            source_page = (root / "wiki/sources/url-aaa111222333.md").read_text(encoding="utf-8")
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

    def test_topic_deposit_writeback_skips_blocked_sources(self):
        # Failures stay recoverable state: only studied sources flip to deposited.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root, with_list=True, with_blocked=True)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            entries = {e["source_id"]: e for e in
                       json.loads((root / "reading-lists/hx.json").read_text(encoding="utf-8"))["entries"]}
            self.assertEqual(entries["url:aaa111222333"]["status"], "deposited")
            self.assertEqual(entries["url:bbb444555666"]["status"], "blocked")
            self.assertEqual(entries["url:bbb444555666"]["blocked_reason"], "paywall")

    def test_same_title_sources_get_distinct_stub_pages(self):
        # Two distinct sources sharing a title must not collide into one stub.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            folder = root / "reports/topic-harness"
            folder.mkdir(parents=True)
            report = folder / "report.md"
            report.write_text("---\nkind: topic\n---\n\n# Harness 综述\n\n正文\n", encoding="utf-8")
            record = {"kind": "topic", "topic_slug": "harness", "title": "Harness",
                      "sources": [{"source_id": "url:abc111abc111", "title": "Harness Engineering",
                                   "url": "https://a.example/one", "source_type": "blog",
                                   "role": "core", "status": "studied"},
                                  {"source_id": "url:def222def222", "title": "Harness Engineering",
                                   "url": "https://b.example/two", "source_type": "blog",
                                   "role": "core", "status": "studied"}],
                      "entities": {}}
            (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            names = sorted(f.name for f in (root / "wiki/sources").glob("*.md"))
            self.assertEqual(names, ["url-abc111abc111.md", "url-def222def222.md"])
            one = (root / "wiki/sources/url-abc111abc111.md").read_text(encoding="utf-8")
            two = (root / "wiki/sources/url-def222def222.md").read_text(encoding="utf-8")
            self.assertIn("url: https://a.example/one", one)
            self.assertIn("source_id: url:abc111abc111", one)
            self.assertIn("url: https://b.example/two", two)
            self.assertIn("source_id: url:def222def222", two)

    def test_paper_link_on_topic_page_stays_out_of_user_notes(self):
        # link_entity must scope generated links to their heading, never leak into ## User notes.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            topic_report = _seed_topic_report(root)
            topic_args = type("A", (), {"input": str(topic_report), "root": str(root)})
            paperwiki.cmd_deposit(topic_args)
            topic_page = root / "wiki/topics/context-compaction.md"
            text = topic_page.read_text(encoding="utf-8")           # simulate a human note
            topic_page.write_text(text.rstrip("\n") + "\n\nhuman insight\n", encoding="utf-8")

            folder = root / "reports/harness-paper"
            folder.mkdir(parents=True)
            paper_report = folder / "report.md"
            paper_report.write_text("# reviewed", encoding="utf-8")
            record = {"paper_id": "arxiv:2500.11111", "title": "Harness Paper",
                      "reading": {"topics": ["Context Compaction"]}}
            (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(paper_report), "root": str(root)}))

            page = topic_page.read_text(encoding="utf-8")
            notes = re.search(r"## User notes\s*(.*?)(?=\n## |\Z)", page, re.S).group(1)
            papers = re.search(r"## Related papers\s*(.*?)(?=\n## |\Z)", page, re.S)
            self.assertIn("human insight", notes)
            self.assertNotIn("arxiv-2500-11111", notes)
            self.assertIsNotNone(papers)
            self.assertIn("- [[arxiv-2500-11111|Harness Paper]]", papers.group(1))

            paperwiki.cmd_deposit(topic_args)                       # rebuild the topic page

            page = topic_page.read_text(encoding="utf-8")
            notes = re.search(r"## User notes\s*(.*?)(?=\n## |\Z)", page, re.S).group(1)
            papers = re.search(r"## Related papers\s*(.*?)(?=\n## |\Z)", page, re.S)
            self.assertIn("human insight", notes)
            self.assertNotIn("arxiv-2500-11111", notes)
            self.assertIn("- [[arxiv-2500-11111|Harness Paper]]", papers.group(1))


if __name__ == "__main__":
    unittest.main()
