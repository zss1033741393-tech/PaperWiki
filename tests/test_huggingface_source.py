import json
import os
import tempfile
import unittest

import paperwiki


# Faithful shape of https://huggingface.co/api/papers/search?q=... (a JSON list;
# each item wraps a `paper` object with id/title/authors/publishedAt/summary/upvotes/ai_summary).
SAMPLE_HF_SEARCH = json.dumps([
    {
        "paper": {
            "id": "2605.15204",
            "title": "SDOF: Taming the Alignment Tax in Multi-Agent Orchestration",
            "authors": [{"name": "Zhantao Wang"}, {"name": "Wei Li"}],
            "publishedAt": "2026-04-20T00:00:00.000Z",
            "summary": "Multi-agent orchestration frameworks route tasks through graph-based pipelines.",
            "upvotes": 7,
            "ai_summary": "SDOF enforces business process constraints via a state machine.",
        },
        "title": "SDOF: Taming the Alignment Tax in Multi-Agent Orchestration",
    },
    {
        "paper": {
            "id": "2505.19591",
            "title": "Multi-Agent Collaboration via Evolving Orchestration",
            "authors": [{"name": "A B"}],
            "publishedAt": "2025-05-26T00:00:00.000Z",
            "summary": "We study evolving orchestration among agents.",
            "upvotes": 8,
        },
    },
])

# Functions this suite monkeypatches; snapshot + restore around each test.
_PATCHED = [
    "fetch", "arxiv_search", "semantic_search", "crossref_search",
    "openalex_search", "huggingface_search", "huggingface_enrich",
]


class HuggingFaceSourceTests(unittest.TestCase):
    def setUp(self):
        self._orig = {name: getattr(paperwiki, name) for name in _PATCHED}

    def tearDown(self):
        for name, fn in self._orig.items():
            setattr(paperwiki, name, fn)

    def test_normalizes_search_records(self):
        paperwiki.fetch = lambda url, binary=False: SAMPLE_HF_SEARCH
        rows = paperwiki.huggingface_search("multi-agent orchestration", 10)
        self.assertEqual(len(rows), 2)
        r = rows[0]
        self.assertEqual(r["arxiv_id"], "2605.15204")
        self.assertEqual(r["year"], 2026)
        self.assertEqual(r["hf_upvotes"], 7)
        self.assertEqual(r["title"], "SDOF: Taming the Alignment Tax in Multi-Agent Orchestration")
        self.assertEqual(r["authors"], ["Zhantao Wang", "Wei Li"])
        self.assertIn("huggingface.co/papers/2605.15204", r["source_url"])
        self.assertEqual(r["provenance"][0]["provider"], "huggingface-search")
        self.assertEqual(r["hf_ai_summary"], "SDOF enforces business process constraints via a state machine.")

    def test_discover_uses_hf_and_tolerates_provider_failures(self):
        def boom(query, limit):
            raise RuntimeError("HTTP Error 429")

        paperwiki.arxiv_search = boom
        paperwiki.semantic_search = boom
        paperwiki.crossref_search = lambda q, n: [
            {"title": "A Crossref Multi-Agent Paper", "doi": "10.1/cr", "year": 2026,
             "provenance": [{"provider": "crossref"}]}]
        paperwiki.openalex_search = lambda q, n: []
        paperwiki.huggingface_search = lambda q, n: [
            {"title": "SDOF Multi-Agent Orchestration 2026", "arxiv_id": "2605.15204",
             "abstract": "orchestration of agents via a state machine", "year": 2026,
             "hf_upvotes": 7, "source_url": "https://huggingface.co/papers/2605.15204",
             "provenance": [{"provider": "huggingface-search"}]}]
        paperwiki.huggingface_enrich = lambda records: []

        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "out.json")
            args = type("A", (), {"query": "multi-agent orchestration", "limit": 5,
                                  "since_years": 2, "no_huggingface": False, "output": out})
            paperwiki.cmd_discover(args)
            with open(out, encoding="utf-8") as f:
                payload = json.load(f)

        titles = [p["title"] for p in payload["papers"]]
        self.assertIn("SDOF Multi-Agent Orchestration 2026", titles)   # HF source contributed
        self.assertIn("A Crossref Multi-Agent Paper", titles)          # survivors merged
        errored = [e["provider"] for e in payload["errors"]]
        self.assertIn("arxiv", errored)                                # failures recorded, not fatal
        self.assertIn("semantic-scholar", errored)


if __name__ == "__main__":
    unittest.main()
