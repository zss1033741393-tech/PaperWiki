"""L1 verification of `recommend`: query derivation + dedup against local wiki pages."""
import json
import tempfile
import unittest
from pathlib import Path

import paperwiki


class RecommendTests(unittest.TestCase):
    def setUp(self):
        self._orig = {n: getattr(paperwiki, n) for n in ("arxiv_search", "crossref_search")}

    def tearDown(self):
        for n, f in self._orig.items():
            setattr(paperwiki, n, f)

    def test_excludes_papers_matching_known_wiki_pages(self):
        """A candidate whose title matches an existing concept page must be dropped
        (ACCEPTANCE: 'a scored reading list distinct from local page identities')."""
        paperwiki.arxiv_search = lambda q, n: [
            {"title": "Agent Memory", "arxiv_id": "2601.00001", "year": 2026, "provenance": []},
            {"title": "A Genuinely New Method", "arxiv_id": "2601.00002", "year": 2026, "provenance": []},
        ]
        paperwiki.crossref_search = lambda q, n: []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "wiki/concepts").mkdir(parents=True)
            (root / "wiki/concepts/agent-memory.md").write_text("# Agent Memory", encoding="utf-8")
            out = root / "rec.json"
            args = type("A", (), {"topic": "agent memory", "limit": 5,
                                  "root": str(root), "output": str(out)})
            paperwiki.cmd_recommend(args)
            recs = json.loads(out.read_text(encoding="utf-8"))["recommendations"]
        titles = [r["title"] for r in recs]
        self.assertIn("A Genuinely New Method", titles)   # novel candidate kept
        self.assertNotIn("Agent Memory", titles)          # already a local page -> excluded

    def test_derives_query_from_topic(self):
        captured = {}
        paperwiki.arxiv_search = lambda q, n: captured.setdefault("q", q) and [] or []
        paperwiki.crossref_search = lambda q, n: []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = root / "rec.json"
            args = type("A", (), {"topic": "multi agent orchestration", "limit": 3,
                                  "root": str(root), "output": str(out)})
            paperwiki.cmd_recommend(args)
        self.assertEqual(captured.get("q"), "multi agent orchestration")


if __name__ == "__main__":
    unittest.main()
