# Report Math Rendering and Finalize Preservation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render report formulas without Markdown corruption and make `finalize` preserve authored deep-reading content while normalizing canonical metadata.

**Architecture:** Protect LaTeX spans before Python Markdown conversion and restore them afterward so KaTeX receives exact source. Refactor `finalize` to distinguish the original scaffold from an authored report, normalize owned frontmatter, merge structured analysis into `record.json`, and call the shared renderer without replacing authored prose.

**Tech Stack:** Python 3 standard library, Python Markdown, KaTeX auto-render, `unittest`, PaperWiki CLI.

---

## File Map

- Modify `scripts/render_report.py`: math extraction/restoration, delimiter validation, reusable HTML renderer.
- Create `tests/test_render_report.py`: renderer regression coverage using real Markdown and generated HTML.
- Modify `paperwiki.py`: authored/scaffold classification, frontmatter normalization, record synchronization, shared renderer invocation.
- Modify `tests/test_finalize.py`: preservation, state, embedded analysis, idempotence, and renderer integration tests.
- Modify `reports/five-ws/{report.md,report.html,record.json}`: normalized canonical artifacts.
- Modify `reports/moc/{report.md,report.html,record.json}`: normalized canonical artifacts and corrected rendering.
- Modify `reports/mars/{report.md,report.html,record.json}`: normalized canonical artifacts and corrected rendering.
- Modify `reports/agentmaster/{report.md,report.html,record.json}`: normalized canonical artifacts and corrected rendering.

### Task 1: Protect LaTeX from Markdown

**Files:**
- Create: `tests/test_render_report.py`
- Modify: `scripts/render_report.py`

- [ ] **Step 1: Write the failing display-math regression test**

```python
import tempfile
import unittest
from pathlib import Path

from scripts.render_report import render


class RenderReportTests(unittest.TestCase):
    def test_preserves_latex_exactly_through_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "report.md"
            output = Path(td) / "report.html"
            formula = r"\mathrm{AvgLogProb}_{ij}=\frac{1}{N}\sum_{k=1}^{N}\log P(t_k)"
            source.write_text(f"# Report\n\n$$\n{formula}\n$$\n", encoding="utf-8")
            render(source, output)
            html = output.read_text(encoding="utf-8")
            self.assertIn(formula, html)
            self.assertNotIn("<em>", html)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
PYTHONPATH=/tmp/paperwiki-python python3 -m unittest tests.test_render_report.RenderReportTests.test_preserves_latex_exactly_through_markdown -v
```

Expected: FAIL because underscores or other LaTeX characters are changed by Markdown.

- [ ] **Step 3: Add failing inline/code-fence and delimiter tests**

```python
def test_preserves_inline_math_but_ignores_code_fences(self):
    source.write_text("Inline $x_i=\\Phi(y_i)$\n\n```text\n$not_math$\n```\n", encoding="utf-8")
    render(source, output)
    html = output.read_text(encoding="utf-8")
    self.assertIn(r"$x_i=\Phi(y_i)$", html)
    self.assertIn("$not_math$", html)

def test_rejects_unpaired_display_delimiter(self):
    source.write_text("# Bad\n\n$$\nx_i\n", encoding="utf-8")
    with self.assertRaisesRegex(ValueError, "Unpaired math delimiter"):
        render(source, output)
```

- [ ] **Step 4: Implement minimal math protection**

Add focused helpers in `scripts/render_report.py`:

```python
MATH_TOKEN = "PAPERWIKI_MATH_{:04d}"

def protect_math(text: str) -> tuple[str, list[str]]:
    formulas = []
    pattern = re.compile(r"```.*?```|\$\$.*?\$\$|(?<!\\)\$(?!\$).*?(?<!\\)\$", re.S)

    def replace(match):
        value = match.group(0)
        if value.startswith("```"):
            return value
        token = MATH_TOKEN.format(len(formulas))
        formulas.append(value)
        return token

    protected = pattern.sub(replace, text)
    if protected.count("$$") or re.search(r"(?<!\\)\$(?!\$)", protected):
        raise ValueError("Unpaired math delimiter in report")
    return protected, formulas

def restore_math(body: str, formulas: list[str]) -> str:
    for index, formula in enumerate(formulas):
        token = MATH_TOKEN.format(index)
        if body.count(token) != 1:
            raise ValueError(f"Math placeholder mismatch: {token}")
        body = body.replace(token, html.escape(formula))
    return body
```

Call `protect_math` before `markdown.markdown` and `restore_math` immediately afterward.

- [ ] **Step 5: Run renderer tests and verify GREEN**

Run:

```bash
PYTHONPATH=/tmp/paperwiki-python python3 -m unittest tests.test_render_report -v
```

Expected: all renderer tests PASS.

- [ ] **Step 6: Commit the renderer change**

```bash
git add scripts/render_report.py tests/test_render_report.py
git commit -m "fix: preserve LaTeX during report rendering"
```

### Task 2: Preserve Authored Reports in Finalize

**Files:**
- Modify: `tests/test_finalize.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Write the failing authored-content preservation test**

```python
def test_preserves_authored_report_body(self):
    with tempfile.TemporaryDirectory() as td:
        report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
        report.write_text(
            "---\npaper_id: arxiv:2511.20639\nstatus: reading\nsource: https://example.test\n---\n\n"
            "# Canonical Paper\n\nSENTINEL DEEP READING\n\n$$\nx_i=\\Phi(y_i)\n$$\n",
            encoding="utf-8",
        )
        paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
        text = report.read_text(encoding="utf-8")
        self.assertIn("SENTINEL DEEP READING", text)
        self.assertIn(r"x_i=\Phi(y_i)", text)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 -m unittest tests.test_finalize.FinalizeTests.test_preserves_authored_report_body -v
```

Expected: FAIL because current `finalize` replaces the sentinel body.

- [ ] **Step 3: Write failing state, embedded-analysis, and idempotence tests**

```python
def test_keeps_unconfirmed_analysis_in_reading_state(self):
    with tempfile.TemporaryDirectory() as td:
        report, ap = _seed_canonical(Path(td), dict(FULL_ANALYSIS))
        report.write_text("# Canonical Paper\n\nAuthored analysis.\n", encoding="utf-8")
        paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
        record = json.loads((report.parent / "record.json").read_text(encoding="utf-8"))
    self.assertEqual(record["status"], "reading")
    self.assertEqual(record["reading"]["analysis_status"], "generated-awaiting-human-confirmation")
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
```

- [ ] **Step 4: Implement report classification and frontmatter normalization**

Add helpers to `paperwiki.py`:

```python
SCAFFOLD_MARKER = "Run `$paper-analyzer`"

def split_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}, text
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, text[match.end():].lstrip("\n")

def normalize_report(text, paper):
    fields, body = split_frontmatter(text)
    fields.update({
        "paper_id": paper["paper_id"],
        "status": "reading",
        "source": paper.get("source_url") or paper.get("pdf_path"),
        "generated": "true",
        "human_confirmed": "false",
    })
    frontmatter = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{frontmatter}\n---\n\n{body.rstrip()}\n"
```

Only construct the short standard report when `SCAFFOLD_MARKER in existing_text`; otherwise normalize and preserve its body.

- [ ] **Step 5: Synchronize record state and use the shared renderer**

In `cmd_finalize`:

```python
p["status"] = "reading"
p.setdefault("reading", {}).update(analysis)
p["reading"]["analysis_status"] = "generated-awaiting-human-confirmation"
side.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

from scripts.render_report import render
render(report, report.with_suffix(".html"))
```

Remove the vendored subprocess/fallback path from `cmd_finalize`.

- [ ] **Step 6: Run finalize tests and verify GREEN**

Run:

```bash
PYTHONPATH=/tmp/paperwiki-python python3 -m unittest tests.test_finalize -v
```

Expected: all finalize tests PASS.

- [ ] **Step 7: Commit finalize behavior**

```bash
git add paperwiki.py tests/test_finalize.py
git commit -m "fix: preserve authored reports during finalize"
```

### Task 3: Migrate and Rebuild Canonical Reports

**Files:**
- Modify: `reports/five-ws/report.md`
- Modify: `reports/five-ws/report.html`
- Modify: `reports/five-ws/record.json`
- Modify: `reports/moc/report.md`
- Modify: `reports/moc/report.html`
- Modify: `reports/moc/record.json`
- Modify: `reports/mars/report.md`
- Modify: `reports/mars/report.html`
- Modify: `reports/mars/record.json`
- Modify: `reports/agentmaster/report.md`
- Modify: `reports/agentmaster/report.html`
- Modify: `reports/agentmaster/record.json`

- [ ] **Step 1: Run corrected finalize for all reports**

```bash
PYTHONPATH=/tmp/paperwiki-python python3 paperwiki.py finalize reports/five-ws/report.md reports/five-ws/analysis.json
PYTHONPATH=/tmp/paperwiki-python python3 paperwiki.py finalize reports/moc/report.md reports/moc/analysis.json
PYTHONPATH=/tmp/paperwiki-python python3 paperwiki.py finalize reports/mars/report.md reports/mars/analysis.json
PYTHONPATH=/tmp/paperwiki-python python3 paperwiki.py finalize reports/agentmaster/report.md reports/agentmaster/analysis.json
```

Expected: each command prints its report path and preserves the long-form body.

- [ ] **Step 2: Verify canonical metadata and idempotence**

Run the four commands a second time, then:

```bash
git diff --check
python3 -m json.tool reports/five-ws/record.json >/dev/null
python3 -m json.tool reports/moc/record.json >/dev/null
python3 -m json.tool reports/mars/record.json >/dev/null
python3 -m json.tool reports/agentmaster/record.json >/dev/null
rg -n '"analysis_status": "generated-awaiting-human-confirmation"' reports/*/record.json
```

Expected: no second-run diff, all JSON parses, and all four records contain the canonical analysis status.

- [ ] **Step 3: Scan HTML for raw or malformed math**

```bash
rg -n '<em>|<p>\$\$|PAPERWIKI_MATH_|\\frac\{1\}\{N\}sum|\{q_i\}\{i=1\}' \
  reports/five-ws/report.html reports/moc/report.html reports/mars/report.html reports/agentmaster/report.html
```

Expected: no malformed-formula matches; valid protected LaTeX remains inside paired delimiters for KaTeX.

- [ ] **Step 4: Run the full suite**

```bash
PYTHONPATH=/tmp/paperwiki-python python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: all tests PASS.

- [ ] **Step 5: Visually inspect formulas**

Open the rebuilt MARS, MOC, and AgentMaster HTML files in the in-app browser. Confirm the user-reported `\sum`, `\Phi`, and decomposition formulas render completely, then inspect every remaining `.katex-display` for visible raw source, clipping, or overflow.

- [ ] **Step 6: Commit canonical artifact migration**

```bash
git add reports/five-ws/report.md reports/five-ws/report.html reports/five-ws/record.json \
  reports/moc/report.md reports/moc/report.html reports/moc/record.json \
  reports/mars/report.md reports/mars/report.html reports/mars/record.json \
  reports/agentmaster/report.md reports/agentmaster/report.html reports/agentmaster/record.json
git commit -m "docs: rebuild reports with preserved math and metadata"
```

### Task 4: Update Existing PR

**Files:**
- No additional repository files.

- [ ] **Step 1: Verify the final branch state**

```bash
git diff origin/dev...HEAD --check
git status -sb
git log --oneline -5
```

Expected: branch contains only intended commits; unrelated `.obsidian/`, `tmp/`, and `wiki/.obsidian/` remain untracked.

- [ ] **Step 2: Push the existing branch**

```bash
git push -u origin codex/five-ws-multi-agent-communication
```

Expected: PR #3 head advances to the final local commit.

- [ ] **Step 3: Update the PR description and add a concise resolution comment**

Update PR #3 to state that formulas are math-protected, authored reports survive `finalize`, records share canonical state/shape, and list fresh test/visual evidence. Do not resolve or reply to nonexistent inline threads; the review feedback is a top-level PR comment.
