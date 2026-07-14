"""L1 verification of `deposit`: reciprocal wikilinks + index/log bookkeeping (wiki 准确)."""
import json
import tempfile
import unittest
from pathlib import Path

import paperwiki


class DepositTests(unittest.TestCase):
    def test_strip_leading_frontmatter_preserves_body_separator(self):
        source = "---\r\ntitle: Example\r\nstatus: reviewed\r\n---\r\n\r\n# Body\r\n\r\nA\r\n\r\n---\r\n\r\nB\r\n"
        result = paperwiki.strip_leading_frontmatter(source)
        self.assertTrue(result.startswith("# Body\r\n"))
        self.assertIn("\r\n---\r\n", result)
        self.assertNotIn("title: Example", result)

    def test_strip_leading_frontmatter_leaves_plain_markdown_unchanged(self):
        source = "# Notes\n\nSummary\n\n---\n\nEvidence\n"
        self.assertEqual(paperwiki.strip_leading_frontmatter(source), source)

    def test_strip_leading_frontmatter_leaves_unclosed_block_unchanged(self):
        source = "---\ntitle: Incomplete\n# Body\n"
        self.assertEqual(paperwiki.strip_leading_frontmatter(source), source)

    def test_deposit_omits_report_frontmatter_from_generated_synthesis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = root / "reports/clean/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "---\npaper_id: arxiv:1234.5678\nstatus: reviewed\n---\n\n"
                "# Clean Paper\n\nBody\n\n---\n\nEvidence\n",
                encoding="utf-8",
            )
            record = {"paper_id": "arxiv:1234.5678", "title": "Clean Paper", "reading": {}}
            (report.parent / "record.json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            synthesis = page.split("## Generated synthesis (draft)\n\n", 1)[1].split("\n## User notes", 1)[0]
            self.assertTrue(page.startswith("---\n"))
            self.assertTrue(synthesis.startswith("# Clean Paper\n"))
            self.assertNotIn("paper_id: arxiv:1234.5678", synthesis)
            self.assertIn("\n---\n", synthesis)

    def test_nested_report_uses_vault_qualified_source_link(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            folder = root / "reports/latentmas"
            folder.mkdir(parents=True)
            report = folder / "report.md"
            report.write_text("# reviewed", encoding="utf-8")
            record = {"paper_id": "arxiv:2511.20639", "title": "LatentMAS",
                      "reading": {"concepts": [], "methods": [],
                                  "datasets": [], "topics": []}}
            (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            paper_page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("[[reports/latentmas/report|LatentMAS report]]", paper_page)

    def test_legacy_sidecar_still_deposits(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = root / "reports/arxiv-1234.md"
            report.parent.mkdir(parents=True)
            report.write_text("# reviewed", encoding="utf-8")
            record = {"paper_id": "arxiv:1234.5678", "title": "Legacy Paper",
                      "reading": {"concepts": [], "methods": [],
                                  "datasets": [], "topics": []}}
            report.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            paper_page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("# Legacy Paper", paper_page)
            self.assertIn("[[reports/arxiv-1234|Legacy Paper report]]", paper_page)

    def test_external_report_uses_explicit_path_instead_of_ambiguous_wikilink(self):
        with tempfile.TemporaryDirectory() as source_td, tempfile.TemporaryDirectory() as vault_td:
            report = Path(source_td) / "report.md"
            report.write_text("# External Notes\n\nSummary", encoding="utf-8")
            root = Path(vault_td)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            paper_page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            self.assertNotIn("[[report]]", paper_page)
            self.assertIn(f"`{report.resolve()}`", paper_page)

    def test_reciprocal_links_and_index_and_log(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reports = root / "reports"
            reports.mkdir()
            report = reports / "x.md"
            report.write_text("# draft", encoding="utf-8")
            record = {"paper_id": "doi:10.1/x", "title": "Linked Paper",
                      "reading": {"concepts": ["Agent Memory"], "methods": [],
                                  "datasets": [], "topics": ["Multi Agent"]}}
            report.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            paper_page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("Agent Memory", paper_page)                 # paper -> concept
            self.assertIn("Multi Agent", paper_page)                  # paper -> topic

            concept = (root / "wiki/concepts/agent-memory.md").read_text(encoding="utf-8")
            self.assertIn("Linked Paper", concept)                    # reciprocal concept -> paper
            self.assertIn("[[doi-10-1-x|", concept)                   # short-name wikilink to the paper

            self.assertIn("Linked Paper", (root / "index.md").read_text(encoding="utf-8"))
            self.assertIn("deposit", (root / "log.md").read_text(encoding="utf-8"))

    def test_uses_obsidian_short_name_wikilinks(self):
        # Obsidian's default link format is shortest-path: [[stem|Alias]], not [[../collection/stem|Alias]].
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            reports = root / "reports"
            reports.mkdir()
            report = reports / "x.md"
            report.write_text("# draft", encoding="utf-8")
            record = {"paper_id": "doi:10.1/x", "title": "Linked Paper",
                      "reading": {"concepts": ["Agent Memory"], "methods": [],
                                  "datasets": [], "topics": []}}
            report.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            paper_page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            concept = (root / "wiki/concepts/agent-memory.md").read_text(encoding="utf-8")
            index = (root / "index.md").read_text(encoding="utf-8")

            self.assertNotIn("[[../", paper_page)                       # no relative-path wikilinks
            self.assertNotIn("[[../", concept)
            self.assertNotIn("[[wiki/papers/", index)
            self.assertIn("[[agent-memory|Agent Memory]]", paper_page)  # paper -> concept, short name
            self.assertIn("[[doi-10-1-x|Linked Paper]]", concept)       # concept -> paper, short name
            self.assertIn("[[doi-10-1-x|Linked Paper]]", index)         # index -> paper, short name

    def test_qualifies_same_stem_entities_across_collections(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = root / "reports/five-ws/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "---\npaper_id: arxiv:2602.11583\nstatus: reading\n"
                "human_confirmed: false\n---\n\n# Five Ws",
                encoding="utf-8",
            )
            record = {
                "paper_id": "arxiv:2602.11583",
                "title": "Five Ws",
                "reading": {
                    "concepts": ["Emergent Language"],
                    "methods": [],
                    "datasets": [],
                    "topics": ["Emergent Language"],
                },
            }
            (report.parent / "record.json").write_text(
                json.dumps(record), encoding="utf-8"
            )

            paperwiki.cmd_deposit(
                type("A", (), {"input": str(report), "root": str(root)})
            )

            page = (root / "wiki/papers/arxiv-2602-11583.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "[[wiki/concepts/emergent-language|Emergent Language]]", page
            )
            self.assertIn(
                "[[wiki/topics/emergent-language|Emergent Language]]", page
            )
            self.assertNotIn("- [[emergent-language|Emergent Language]]", page)


if __name__ == "__main__":
    unittest.main()
