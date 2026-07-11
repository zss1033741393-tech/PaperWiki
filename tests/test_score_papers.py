import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "skills" / "discover-papers" / "scripts" / "score_papers.py"
SPEC = importlib.util.spec_from_file_location("score_papers", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScorePapersTests(unittest.TestCase):
    def test_full_evidence_score(self):
        record = {"discovery": {"signals": {key: 1 for key in MODULE.WEIGHTS}}}
        result = MODULE.score(record)
        self.assertAlmostEqual(result["discovery"]["score"], 1)
        self.assertEqual(result["discovery"]["band"], "must-read")

    def test_missing_signal_is_renormalized(self):
        record = {"discovery": {"signals": {"relevance": 1, "recency": 1}}}
        result = MODULE.score(record)
        self.assertAlmostEqual(result["discovery"]["score"], 1)
        self.assertAlmostEqual(result["discovery"]["coverage"], 0.45)
        self.assertEqual(result["discovery"]["band"], "recommended")

    def test_out_of_range_signal_fails(self):
        with self.assertRaises(ValueError):
            MODULE.score({"discovery": {"signals": {"relevance": 2}}})


if __name__ == "__main__":
    unittest.main()

