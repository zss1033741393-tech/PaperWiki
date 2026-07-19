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


SOURCE_ANALYSIS = {
    "tldr": "one line", "research_question": "Q", "contributions": ["C"], "method": "M",
    "findings": ["F"], "limitations": ["L"], "concepts": ["Context Rot"],
    "methods": ["Compaction"], "topics": ["Context Engineering"], "open_questions": ["Q?"],
}


def _seed_source(root, analysis):
    folder = root / "reports/ece"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "report.md"
    report.write_text("# draft", encoding="utf-8")
    record = {"paper_id": "url:abcdef123456", "title": "Effective Context Engineering",
              "kind": "source", "source_type": "blog",
              "source_url": "https://www.anthropic.com/engineering/x",
              "reading": {"report_path": str(report)}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    ap = folder / "analysis.json"
    ap.write_text(json.dumps(analysis), encoding="utf-8")
    return report, ap


class FinalizeTests(unittest.TestCase):
    def test_preserves_authored_report_body(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            report.write_text(
                "---\npaper_id: arxiv:2511.20639\nstatus: reading\n"
                "source: https://example.test\n---\n\n"
                "# Canonical Paper\n\nSENTINEL DEEP READING\n\n"
                "$$\nx_i=\\Phi(y_i)\n$$\n",
                encoding="utf-8",
            )

            paperwiki.cmd_finalize(type("A", (), {
                "report": str(report), "analysis": str(ap),
            }))

            text = report.read_text(encoding="utf-8")
            self.assertIn("SENTINEL DEEP READING", text)
            self.assertIn(r"x_i=\Phi(y_i)", text)

    def test_keeps_unconfirmed_analysis_in_reading_state(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            report.write_text("# Canonical Paper\n\nAuthored analysis.\n", encoding="utf-8")

            paperwiki.cmd_finalize(type("A", (), {
                "report": str(report), "analysis": str(ap),
            }))

            record = json.loads((report.parent / "record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "reading")
            self.assertEqual(
                record["reading"]["analysis_status"],
                "generated-awaiting-human-confirmation",
            )
            self.assertEqual(record["reading"]["findings"], FULL_ANALYSIS["findings"])

    def test_finalize_is_idempotent_for_authored_report(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            report.write_text("# Canonical Paper\n\nAuthored analysis.\n", encoding="utf-8")
            args = type("A", (), {"report": str(report), "analysis": str(ap)})

            paperwiki.cmd_finalize(args)
            first_report = report.read_bytes()
            first_record = (report.parent / "record.json").read_bytes()
            paperwiki.cmd_finalize(args)

            self.assertEqual(report.read_bytes(), first_report)
            self.assertEqual((report.parent / "record.json").read_bytes(), first_record)

    def test_uses_sibling_record_json(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            record = json.loads((report.parent / "record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "reading")
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

    def test_copies_valid_external_analysis_into_canonical_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report, canonical_analysis = _seed_canonical(root, dict(FULL_ANALYSIS))
            canonical_analysis.unlink()
            external_analysis = root / "reviewed-analysis.json"
            external_analysis.write_text(json.dumps(FULL_ANALYSIS), encoding="utf-8")

            paperwiki.cmd_finalize(type("A", (), {
                "report": str(report),
                "analysis": str(external_analysis),
            }))

            self.assertTrue(canonical_analysis.exists())
            self.assertEqual(
                json.loads(canonical_analysis.read_text(encoding="utf-8")),
                FULL_ANALYSIS,
            )

    def test_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(FULL_ANALYSIS)
            del incomplete["findings"]
            report, ap = _seed(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("findings", str(cm.exception))

    def test_marks_reading_and_human_unconfirmed(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed(Path(td), dict(FULL_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            text = report.read_text(encoding="utf-8")
            self.assertIn("status: reading", text)
            self.assertIn("human_confirmed: false", text)
            side = json.loads(report.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(side["status"], "reading")
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


class FinalizeSourceTests(unittest.TestCase):
    def test_source_analysis_passes_without_paper_only_fields(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_source(Path(td), dict(SOURCE_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            text = report.read_text(encoding="utf-8")
            self.assertIn("status: reading", text)

    def test_source_scaffold_uses_neutral_source_sections(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_source(Path(td), dict(SOURCE_ANALYSIS))

            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))

            text = report.read_text(encoding="utf-8")
            self.assertIn("## 来源信息与阅读范围", text)
            self.assertIn("## 关键观点与证据", text)
            self.assertIn("## 局限与适用边界", text)
            self.assertNotIn("## 论文信息", text)
            self.assertNotIn("## 实验与证据", text)
            self.assertNotIn("[!summary]", text)

    def test_source_analysis_still_requires_core_fields(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(SOURCE_ANALYSIS)
            del incomplete["findings"]
            report, ap = _seed_source(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("findings", str(cm.exception))

    def test_paper_analysis_gate_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(FULL_ANALYSIS)
            del incomplete["experiments"]
            report, ap = _seed(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("experiments", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
