"""L1 characterization + verification of the discovery scoring engine (发现质量)."""
import datetime as dt
import unittest

import paperwiki

YEAR = dt.date.today().year


def sig(record, query="multi agent orchestration"):
    return paperwiki.score(dict(record), query)["discovery"]


class ScoringTests(unittest.TestCase):
    def test_flags_retracted_or_withdrawn_titles(self):
        self.assertIn("possible-retraction-or-withdrawal",
                      paperwiki.score({"title": "A RETRACTED study of agents", "year": YEAR}, "agents")["quality_flags"])
        self.assertIn("possible-retraction-or-withdrawal",
                      paperwiki.score({"title": "Withdrawn: multi-agent work", "year": YEAR}, "agents")["quality_flags"])
        self.assertEqual([],
                         paperwiki.score({"title": "A normal multi-agent paper", "year": YEAR}, "agents")["quality_flags"])

    def test_recency_decays_linearly_over_four_years_then_clamps_to_zero(self):
        self.assertAlmostEqual(sig({"title": "x", "year": YEAR})["signals"]["recency"], 1.0)
        self.assertAlmostEqual(sig({"title": "x", "year": YEAR - 2})["signals"]["recency"], 0.5)
        self.assertEqual(sig({"title": "x", "year": YEAR - 10})["signals"]["recency"], 0.0)

    def test_citation_signal_is_monotonic_and_relevance_scaled(self):
        # citations stay monotonic in count for a fixed relevant title; post-O2 the signal is
        # scaled by relevance, so it is capped at the title's relevance rather than at 1.0.
        rec = lambda c: {"title": "multi agent orchestration", "year": YEAR, "citation_count": c}
        rel = sig(rec(0))["signals"]["relevance"]
        s = lambda c: sig(rec(c))["signals"]["citations"]
        self.assertLess(s(0), s(10))
        self.assertLess(s(10), s(100))
        self.assertLessEqual(s(100000), rel + 1e-9)
        self.assertGreater(s(100000), 0.9 * rel)

    def test_citations_absent_is_missing_not_zero(self):
        d = sig({"title": "x", "year": YEAR})
        self.assertIsNone(d["signals"]["citations"])
        self.assertIn("citations", d["missing_evidence"])

    def test_venue_tiers(self):
        self.assertEqual(sig({"title": "x", "year": YEAR, "venue": "NeurIPS 2026"})["signals"]["venue"], 0.95)
        self.assertEqual(sig({"title": "x", "year": YEAR, "venue": "Some Local Workshop"})["signals"]["venue"], 0.65)
        self.assertIsNone(sig({"title": "x", "year": YEAR})["signals"]["venue"])

    def test_coverage_confidence_adjustment_dampens_thin_evidence(self):
        thin = sig({"title": "multi agent orchestration", "year": YEAR})  # only relevance + recency
        self.assertLess(thin["coverage"], 0.5)
        self.assertLess(thin["score"], thin["raw_score"])  # confidence-adjusted downward

    def test_strong_paper_reaches_must_read_band(self):
        d = sig({"title": "multi agent orchestration", "year": YEAR,
                 "abstract": "multi agent orchestration with code available at github.com/x/y",
                 "venue": "NeurIPS", "citation_count": 500, "hf_upvotes": 80})
        self.assertGreaterEqual(d["coverage"], 0.7)
        self.assertEqual(d["band"], "must-read")

    def test_unrelated_stale_paper_is_watch_band(self):
        d = sig({"title": "unrelated topic", "year": YEAR - 10}, "quantum photonics")
        self.assertEqual(d["band"], "watch")

    def test_citation_contribution_is_scaled_by_relevance(self):
        # Finding O2: raw citation count must not let an off-topic paper outrank relevant ones.
        # For the SAME citation count, an on-topic paper's citation signal must dominate an
        # off-topic paper's (citations count only in proportion to relevance).
        on = sig({"title": "multi agent orchestration for reasoning", "year": YEAR, "citation_count": 1000})["signals"]["citations"]
        off = sig({"title": "a study of unrelated photonics", "year": YEAR, "citation_count": 1000})["signals"]["citations"]
        self.assertGreater(on, off * 2)


if __name__ == "__main__":
    unittest.main()
