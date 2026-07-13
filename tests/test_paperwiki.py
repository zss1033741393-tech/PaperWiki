import tempfile
import unittest
import json
import subprocess
from pathlib import Path
import paperwiki


class PaperWikiTests(unittest.TestCase):
    def test_report_slug_and_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertEqual(paperwiki.report_slug("LatentMAS"), "latentmas")
            self.assertEqual(
                paperwiki.report_slug("Graph of Agents: A Survey"),
                "graph-of-agents-a-survey",
            )
            paths = paperwiki.report_paths(root, "LatentMAS")
            self.assertEqual(paths["report"], root / "reports/latentmas/report.md")
            self.assertEqual(paths["record"], root / "reports/latentmas/record.json")

    def test_record_path_prefers_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / "reports/latentmas"
            folder.mkdir(parents=True)
            report = folder / "report.md"
            canonical = folder / "record.json"
            legacy = folder / "report.json"
            canonical.write_text("{}", encoding="utf-8")
            legacy.write_text("{}", encoding="utf-8")
            self.assertEqual(paperwiki.resolve_record_path(report), canonical)

    def test_record_path_accepts_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "arxiv-1234.md"
            legacy = report.with_suffix(".json")
            legacy.write_text("{}", encoding="utf-8")
            self.assertEqual(paperwiki.resolve_record_path(report), legacy)

    def test_record_path_reports_canonical_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "reports/latentmas/report.md"
            self.assertEqual(
                paperwiki.resolve_record_path(report),
                report.parent / "record.json",
            )

    def test_read_uses_explicit_report_slug(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdf = root / "A Long Local Paper Title.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            args = type("A", (), {
                "paper": str(pdf),
                "root": str(root),
                "report_slug": "LatentMAS",
            })

            paperwiki.cmd_read(args)

            report = root / "reports/latentmas/report.md"
            record = root / "reports/latentmas/record.json"
            self.assertTrue(report.exists())
            self.assertTrue(record.exists())
            self.assertEqual(
                json.loads(record.read_text(encoding="utf-8"))["reading"]["report_path"],
                str(report),
            )

    def test_read_uses_title_slug_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdf = root / "Graph of Agents.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            args = type("A", (), {
                "paper": str(pdf),
                "root": str(root),
                "report_slug": None,
            })

            paperwiki.cmd_read(args)

            self.assertTrue((root / "reports/graph-of-agents/report.md").exists())
            self.assertTrue((root / "reports/graph-of-agents/record.json").exists())

    def test_gitignore_tracks_only_canonical_report_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            source = Path(paperwiki.__file__).with_name(".gitignore")
            (root / ".gitignore").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            folder = root / "reports/latentmas"
            folder.mkdir(parents=True)
            canonical = ["report.md", "report.html", "analysis.json", "record.json"]
            for name in canonical + ["notes.tmp"]:
                (folder / name).write_text("x", encoding="utf-8")

            for name in canonical:
                result = subprocess.run(
                    ["git", "check-ignore", "-q", f"reports/latentmas/{name}"],
                    cwd=root,
                )
                self.assertEqual(result.returncode, 1, name)
            ignored = subprocess.run(
                ["git", "check-ignore", "-q", "reports/latentmas/notes.tmp"],
                cwd=root,
            )
            self.assertEqual(ignored.returncode, 0)

    def test_identity_precedence(self):
        self.assertEqual(paperwiki.paper_id({"title":"X","doi":"10.1/ABC","arxiv_id":"1234.5678"}), "doi:10.1/abc")
        self.assertEqual(paperwiki.paper_id({"title":"X","arxiv_id":"1234.5678v2"}), "arxiv:1234.5678")

    def test_merge_duplicate_arxiv(self):
        rows=paperwiki.merge([
            {"title":"Test","arxiv_id":"1234.5678","provenance":[{"provider":"a"}]},
            {"title":"Test","arxiv_id":"1234.5678v2","venue":"X","provenance":[{"provider":"b"}]},
        ])
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["venue"],"X"); self.assertEqual(len(rows[0]["provenance"]),2)

    def test_merge_doi_record_with_arxiv_only_record(self):
        rows=paperwiki.merge([
            {"title":"Same Paper","arxiv_id":"1234.5678","provenance":[{"provider":"arxiv"}]},
            {"title":"Same Paper","arxiv_id":"1234.5678","doi":"10.1/same","citation_count":10,"provenance":[{"provider":"openalex"}]},
        ])
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["paper_id"],"doi:10.1/same"); self.assertEqual(rows[0]["citation_count"],10)

    def test_score_exposes_all_dimensions_and_missing_evidence(self):
        result=paperwiki.score({"title":"A new agent memory method","abstract":"Code is available at github.com/x/y","year":2026,"hf_upvotes":25,"hf_url":"https://huggingface.co/papers/x","provenance":[]},"agent memory")
        self.assertEqual(set(result["discovery"]["signals"]),set(paperwiki.WEIGHTS))
        self.assertIn("author_continuity",result["discovery"]["missing_evidence"])
        self.assertNotIn("novelty",result["discovery"]["missing_evidence"])
        self.assertGreater(result["discovery"]["signals"]["reproducibility"],0)
        self.assertGreater(result["discovery"]["signals"]["novelty"],0)
        self.assertLess(result["discovery"]["score"],result["discovery"]["raw_score"])

    def test_deposit_is_idempotent_and_preserves_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); report=root/"report.md"; report.write_text("# Test Paper\n\nSummary",encoding="utf-8")
            args=type("A",(),{"input":str(report),"root":str(root)})
            paperwiki.cmd_deposit(args); target=next((root/"wiki/papers").glob("*.md"))
            target.write_text(target.read_text(encoding="utf-8").replace("## User notes\n\n","## User notes\n\nMy insight\n"),encoding="utf-8")
            paperwiki.cmd_deposit(args)
            self.assertEqual(len(list((root/"wiki/papers").glob("*.md"))),1)
            self.assertIn("My insight",target.read_text(encoding="utf-8"))

    def test_finalize_and_link_entities(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); reports=root/"reports"; reports.mkdir(); report=reports/"x.md"
            report.write_text("# draft",encoding="utf-8")
            record={"paper_id":"doi:10.1/x","title":"Linked Paper","authors":["A"],"year":2026,"source_url":"https://doi.org/10.1/x","reading":{"report_path":str(report)}}
            report.with_suffix(".json").write_text(json.dumps(record),encoding="utf-8")
            analysis={"tldr":"Result","research_question":"Why?","contributions":["C"],"method":"M","experiments":["E"],"findings":["F"],"limitations":["L"],"reproducibility":["R"],"concepts":["Memory Agent"],"methods":["Retrieval"],"datasets":["Bench"],"topics":["Agent Memory"],"open_questions":["Q"]}
            ap=root/"analysis.json"; ap.write_text(json.dumps(analysis),encoding="utf-8")
            paperwiki.cmd_finalize(type("A",(),{"report":str(report),"analysis":str(ap)}))
            paperwiki.cmd_deposit(type("A",(),{"input":str(report),"root":str(root)}))
            page=next((root/"wiki/papers").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("Memory Agent",page); self.assertTrue((root/"wiki/concepts/memory-agent.md").exists())
            self.assertTrue(report.with_suffix(".html").exists())


if __name__ == "__main__": unittest.main()
