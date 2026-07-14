"""Regression tests for Markdown-to-HTML report rendering."""

import tempfile
import unittest
from pathlib import Path

from scripts.render_report import render


class RenderReportTests(unittest.TestCase):
    def _render(self, markdown_text):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        source = Path(tempdir.name) / "report.md"
        output = Path(tempdir.name) / "report.html"
        source.write_text(markdown_text, encoding="utf-8")
        render(source, output)
        return output.read_text(encoding="utf-8")

    def test_preserves_display_latex_exactly_through_markdown(self):
        formula = r"\mathrm{AvgLogProb}_{ij}=\frac{1}{N}\sum_{k=1}^{N}\log P(t_k)"

        rendered = self._render(f"# Report\n\n$$\n{formula}\n$$\n")

        self.assertIn(formula, rendered)
        self.assertNotIn("<em>", rendered)

    def test_preserves_inline_math_and_ignores_code_fences(self):
        rendered = self._render(
            "# Report\n\n"
            r"Inline $x_i=\Phi(y_i)$ stays mathematical."
            "\n\n```text\n$not_math$ and $$not_display_math$$\n```\n"
        )

        self.assertIn(r"$x_i=\Phi(y_i)$", rendered)
        self.assertIn("$not_math$ and $$not_display_math$$", rendered)

    def test_preserves_agentmaster_decomposition_formula(self):
        formula = (
            r"q \xrightarrow{g_{complex}} \{q_i\}_{i=1}^{n},\quad "
            r"a_i=f_{r(q_i)}(q_i;\mathcal T_{r(q_i)})"
        )

        rendered = self._render(f"# Report\n\n$$\n{formula}\n$$\n")

        self.assertIn(formula, rendered)

    def test_rejects_unpaired_display_delimiter(self):
        with self.assertRaisesRegex(ValueError, "Unpaired math delimiter"):
            self._render("# Bad report\n\n$$\nx_i=1\n")


if __name__ == "__main__":
    unittest.main()
