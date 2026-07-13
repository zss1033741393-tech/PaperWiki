"""L1 verification of `finalize`: schema gate, review status, mermaid fallback, HTML render."""
import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import paperwiki

FULL_ANALYSIS = {
    "tldr": "one line", "research_question": "Q", "contributions": ["C"], "method": "M",
    "experiments": ["E"], "findings": ["F"], "limitations": ["L"], "reproducibility": ["R"],
    "concepts": ["Agent Memory"], "methods": ["Retrieval"], "datasets": ["Bench"],
    "topics": ["Multi Agent"], "open_questions": ["Q?"],
}


def _seed(root, analysis):
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / "x.md"
    report.write_text("# draft", encoding="utf-8")
    record = {"paper_id": "doi:10.1/x", "title": "Linked Paper", "authors": ["A"],
              "year": 2026, "source_url": "https://doi.org/10.1/x",
              "reading": {"report_path": str(report)}}
    report.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")
    ap = root / "analysis.json"
    ap.write_text(json.dumps(analysis), encoding="utf-8")
    return report, ap


def _seed_canonical(root, analysis):
    folder = root / "reports/latentmas"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "report.md"
    report.write_text("# draft", encoding="utf-8")
    record = {"paper_id": "arxiv:2511.20639", "title": "Canonical Paper", "authors": ["A"],
              "year": 2026, "source_url": "https://arxiv.org/abs/2511.20639",
              "reading": {"report_path": str(report)}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    ap = folder / "analysis.json"
    ap.write_text(json.dumps(analysis), encoding="utf-8")
    return report, ap


class FinalizeTests(unittest.TestCase):
    def test_uses_sibling_record_json(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            record = json.loads((report.parent / "record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "reviewed")
            self.assertTrue((report.parent / "report.html").exists())

    def test_canonical_record_wins_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            legacy = {"paper_id": "doi:10.1/legacy", "title": "Legacy Paper", "authors": [],
                      "reading": {"report_path": str(report)}}
            report.with_suffix(".json").write_text(json.dumps(legacy), encoding="utf-8")
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))

            self.assertIn("# Canonical Paper", report.read_text(encoding="utf-8"))
            self.assertIn("Using canonical reading record", stderr.getvalue())
            self.assertEqual(
                json.loads(report.with_suffix(".json").read_text(encoding="utf-8"))["title"],
                "Legacy Paper",
            )

    def test_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(FULL_ANALYSIS)
            del incomplete["findings"]
            report, ap = _seed(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("findings", str(cm.exception))

    def test_marks_reviewed_and_human_unconfirmed(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed(Path(td), dict(FULL_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            text = report.read_text(encoding="utf-8")
            self.assertIn("status: reviewed", text)
            self.assertIn("human_confirmed: false", text)
            side = json.loads(report.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(side["status"], "reviewed")
            self.assertEqual(side["reading"]["analysis_status"], "generated-awaiting-human-confirmation")

    def test_mermaid_fallback_when_absent(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed(Path(td), dict(FULL_ANALYSIS))  # no "mermaid" key
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("flowchart LR", report.read_text(encoding="utf-8"))

    def test_generates_html_sibling(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed(Path(td), dict(FULL_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertTrue(report.with_suffix(".html").exists())


if __name__ == "__main__":
    unittest.main()
