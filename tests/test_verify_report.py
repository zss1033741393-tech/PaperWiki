"""Contract tests for the reusable paper-report verification gate."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = ROOT / "skills" / "read-paper" / "scripts" / "verify_report.py"
VERIFY_COMMAND = "python skills/read-paper/scripts/verify_report.py"


class VerifyReportCliTests(unittest.TestCase):
    def _run(self, markdown_text, html_text, *, pass_directory=False):
        with tempfile.TemporaryDirectory() as tempdir:
            report_dir = Path(tempdir) / "sample"
            report_dir.mkdir()
            report = report_dir / "report.md"
            report.write_text(markdown_text, encoding="utf-8")
            (report_dir / "report.html").write_text(html_text, encoding="utf-8")
            target = report_dir if pass_directory else report
            return subprocess.run(
                [sys.executable, str(VERIFY_SCRIPT), str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_report_directory_and_counts_preserved_formulas(self):
        formula = r"$$\mathrm{Avg}_{i}=\frac{1}{N}\sum_{k=1}^{N}x_k$$"

        result = self._run(
            f"# Report\n\n{formula}\n",
            f"<article><p>{formula}</p></article>",
            pass_directory=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("formulas=1", result.stdout)
        self.assertIn("status=ok", result.stdout)

    def test_rejects_html_that_does_not_preserve_formula_exactly(self):
        result = self._run(
            r"# Report\n\n$$x_i=\Phi(y_i)$$\n",
            "<article><p>formula missing</p></article>",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("formula 1 is missing or changed", result.stderr)

    def test_rejects_unpaired_math_delimiter(self):
        result = self._run("# Report\n\n$$\nx_i=1\n", "<article></article>")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unpaired math delimiter", result.stderr)

    def test_rejects_stale_math_placeholder_in_html(self):
        result = self._run(
            "# Report without math\n",
            "<article>PAPERWIKIMATH0TOKEN</article>",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved math placeholder", result.stderr)


class FormulaGateDocumentationTests(unittest.TestCase):
    def test_read_paper_skill_requires_the_formula_gate(self):
        skill = (ROOT / "skills" / "read-paper" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Completion Gate", skill)
        self.assertIn(VERIFY_COMMAND, skill)
        self.assertIn(".katex-error", skill)

    def test_root_agent_rules_require_the_formula_gate(self):
        rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn(VERIFY_COMMAND, rules)
        self.assertIn("report.md", rules)
        self.assertIn("report.html", rules)
        self.assertIn("human confirmation", rules)


if __name__ == "__main__":
    unittest.main()
