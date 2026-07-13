import types
import unittest

import paperwiki


class BroaderProvidersTests(unittest.TestCase):
    """paper-search-mcp legal-provider layer (opt-in, gracefully degrading, Sci-Hub excluded)."""

    def test_scihub_is_excluded_from_legal_platforms(self):
        self.assertIn("dblp", paperwiki.LEGAL_PSM_PLATFORMS)
        self.assertNotIn("sci_hub", paperwiki.LEGAL_PSM_PLATFORMS)
        self.assertNotIn("scihub", paperwiki.LEGAL_PSM_PLATFORMS)

    def test_normalizes_injected_paper_object(self):
        fake = types.SimpleNamespace(
            title="DBLP Multi-Agent Paper", authors=["X Y", "Z W"], abstract="",
            doi="10.1/z", pdf_url="", url="https://dblp.org/rec/abc",
            published_date=None, source="dblp", extra={"venue": "AAAI", "year": "2026"})

        class Searcher:
            def search(self, q, n):
                return [fake]

        rows = paperwiki.broader_search("multi-agent", 5, searchers={"dblp": Searcher()})
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["title"], "DBLP Multi-Agent Paper")
        self.assertEqual(r["authors"], ["X Y", "Z W"])
        self.assertEqual(r["year"], 2026)
        self.assertEqual(r["venue"], "AAAI")
        self.assertEqual(r["doi"], "10.1/z")
        self.assertEqual(r["provenance"][0]["provider"], "psm-dblp")

    def test_tolerates_per_searcher_failure(self):
        class Boom:
            def search(self, q, n):
                raise RuntimeError("503 Service Unavailable")

        rows = paperwiki.broader_search("multi-agent", 5, searchers={"dblp": Boom()})
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
