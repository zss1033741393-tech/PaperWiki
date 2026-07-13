# Deposit Synthesis Frontmatter Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove only a source report's leading YAML frontmatter before embedding it in a Wiki paper synthesis, and clean the same artifact from the existing LatentMAS and Graph-of-Agents pages.

**Architecture:** Add one pure Markdown boundary helper to `paperwiki.py` and call it only when composing `Generated synthesis (draft)`. Preserve the original input for metadata resolution. Migrate the two existing generated pages with targeted edits rather than re-running deposit, so operation logs and unrelated content do not change.

**Tech Stack:** Python 3 standard library, regular expressions, `unittest`, Markdown/Obsidian.

---

### Task 1: Define and implement the frontmatter parsing contract

**Files:**
- Modify: `tests/test_deposit.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Write failing pure-helper tests**

Add these tests to `DepositTests`:

```python
def test_strip_leading_frontmatter_preserves_body_separator(self):
    source = "---\r\ntitle: Example\r\nstatus: reviewed\r\n---\r\n\r\n# Body\r\n\r\nA\r\n\r\n---\r\n\r\nB\r\n"
    result = paperwiki.strip_leading_frontmatter(source)
    self.assertTrue(result.startswith("# Body\r\n"))
    self.assertIn("\r\n---\r\n", result)
    self.assertNotIn("title: Example", result)

def test_strip_leading_frontmatter_leaves_plain_markdown_unchanged(self):
    source = "# Notes\n\nSummary\n\n---\n\nEvidence\n"
    self.assertEqual(paperwiki.strip_leading_frontmatter(source), source)

def test_strip_leading_frontmatter_leaves_unclosed_block_unchanged(self):
    source = "---\ntitle: Incomplete\n# Body\n"
    self.assertEqual(paperwiki.strip_leading_frontmatter(source), source)
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_deposit.DepositTests.test_strip_leading_frontmatter_preserves_body_separator \
  tests.test_deposit.DepositTests.test_strip_leading_frontmatter_leaves_plain_markdown_unchanged \
  tests.test_deposit.DepositTests.test_strip_leading_frontmatter_leaves_unclosed_block_unchanged -v
```

Expected: three errors because `paperwiki.strip_leading_frontmatter` does not exist.

- [ ] **Step 3: Implement the minimal pure helper**

Add immediately before `cmd_deposit` in `paperwiki.py`:

```python
def strip_leading_frontmatter(text):
    match = re.match(
        r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n(?:[ \t]*\r?\n)?)?",
        text,
        re.S,
    )
    return text[match.end():] if match else text
```

The pattern is anchored at the start, accepts LF/CRLF and delimiter whitespace, consumes at most one following blank line, and cannot remove internal separators when the document does not begin with frontmatter.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python3 -m unittest tests.test_deposit -v`

Expected: all deposit tests pass.

- [ ] **Step 5: Commit the parsing contract**

```bash
git add paperwiki.py tests/test_deposit.py
git commit -m "test: define report frontmatter cleanup"
```

### Task 2: Sanitize only the generated synthesis boundary

**Files:**
- Modify: `tests/test_deposit.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Write a failing deposit integration test**

Add this test to `DepositTests`:

```python
def test_deposit_omits_report_frontmatter_from_generated_synthesis(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        report = root / "reports/clean/report.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\npaper_id: arxiv:1234.5678\nstatus: reviewed\n---\n\n"
            "# Clean Paper\n\nBody\n\n---\n\nEvidence\n",
            encoding="utf-8",
        )
        record = {"paper_id": "arxiv:1234.5678", "title": "Clean Paper", "reading": {}}
        (report.parent / "record.json").write_text(json.dumps(record), encoding="utf-8")

        paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

        page = next((root / "wiki/papers").glob("*.md")).read_text(encoding="utf-8")
        synthesis = page.split("## Generated synthesis (draft)\n\n", 1)[1].split("\n## User notes", 1)[0]
        self.assertTrue(page.startswith("---\n"))
        self.assertTrue(synthesis.startswith("# Clean Paper\n"))
        self.assertNotIn("paper_id: arxiv:1234.5678", synthesis)
        self.assertIn("\n---\n", synthesis)
```

- [ ] **Step 2: Run the integration test and verify RED**

Run: `python3 -m unittest tests.test_deposit.DepositTests.test_deposit_omits_report_frontmatter_from_generated_synthesis -v`

Expected: failure because the generated synthesis still begins with the source report's `---` block.

- [ ] **Step 3: Integrate the helper at the synthesis boundary**

In `cmd_deposit`, derive a sanitized value immediately before constructing `body`:

```python
synthesis_text = strip_leading_frontmatter(text)
```

Replace only the generated synthesis interpolation from `{text}` to `{synthesis_text}`. Keep `text` unchanged for the record-free title fallback and provenance path.

- [ ] **Step 4: Run deposit and full tests (GREEN)**

Run: `python3 -m unittest tests.test_deposit tests.test_paperwiki -v`

Expected: all deposit/integration tests pass, including user-note preservation.

Run: `python3 -m unittest discover -s tests -q`

Expected: all tests pass.

- [ ] **Step 5: Commit the deposit behavior**

```bash
git add paperwiki.py tests/test_deposit.py
git commit -m "fix: omit report metadata from wiki synthesis"
```

### Task 3: Clean existing Wiki pages and deliver the PR update

**Files:**
- Modify: `wiki/papers/arxiv-2511-20639.md`
- Modify: `wiki/papers/arxiv-2604-17148.md`
- Modify: `docs/superpowers/specs/2026-07-13-deposit-frontmatter-cleanup-design.md`

- [ ] **Step 1: Locate the two embedded frontmatter blocks**

Run:

```bash
python3 -c 'from pathlib import Path
for p in (Path("wiki/papers/arxiv-2511-20639.md"), Path("wiki/papers/arxiv-2604-17148.md")):
    text=p.read_text(encoding="utf-8")
    synthesis=text.split("## Generated synthesis (draft)\n\n",1)[1].split("\n## User notes",1)[0]
    assert synthesis.startswith("---\n"), p
    print(p)'
```

Expected: both Wiki paths print and both assertions pass before migration.

- [ ] **Step 2: Remove only the embedded leading block from each synthesis**

For each page, keep the first page-level YAML block unchanged. Inside `Generated synthesis (draft)`, delete the leading report block from its opening `---` through its closing `---` and the following blank line. The synthesis must then begin with the paper's `# <title>` heading. Do not change `log.md`.

- [ ] **Step 3: Mark the design implemented**

Change the design document status to:

```text
Status: Approved and implemented on `dev`
```

- [ ] **Step 4: Verify migrated content and repository health**

Run:

```bash
python3 -c 'from pathlib import Path
for p in (Path("wiki/papers/arxiv-2511-20639.md"), Path("wiki/papers/arxiv-2604-17148.md")):
    text=p.read_text(encoding="utf-8")
    assert text.startswith("---\n"), p
    synthesis=text.split("## Generated synthesis (draft)\n\n",1)[1].split("\n## User notes",1)[0]
    assert synthesis.startswith("# "), p
    assert not synthesis.startswith("---"), p
    print(p, "OK")'
```

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `PYTHONPYCACHEPREFIX=/tmp/paperwiki-frontmatter-pycache python3 -m py_compile paperwiki.py`

Expected: exit code 0.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 5: Commit and push the migration**

```bash
git add wiki/papers/arxiv-2511-20639.md wiki/papers/arxiv-2604-17148.md docs/superpowers/specs/2026-07-13-deposit-frontmatter-cleanup-design.md
git commit -m "content: clean embedded report frontmatter"
git push origin dev
```

Expected: `origin/dev` advances and the existing `dev → main` PR updates.
