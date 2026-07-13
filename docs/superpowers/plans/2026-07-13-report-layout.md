# Semantic Paper Report Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move paper reports into abbreviation-named directories with four versioned semantic artifacts, while retaining compatibility with legacy flat reports.

**Architecture:** Centralize report/record path rules in small helpers inside `paperwiki.py`. The `read`, `finalize`, and `deposit` commands use those helpers so new reports follow `reports/<slug>/{report.md,record.json}` and old same-stem sidecars still work. Deposit derives an Obsidian vault-qualified source target from the report path. Existing artifacts are migrated only after the behavior is covered by tests.

**Tech Stack:** Python 3 standard library, `unittest`, Git ignore rules, Markdown/Obsidian wikilinks.

---

## Task 1: Establish a clean baseline and report-path helper contract

**Files:**
- Modify: `tests/test_paperwiki.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Verify the existing suite is green**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 32 tests` and `OK`.

- [ ] **Step 2: Write failing helper tests**

Add tests proving:

```python
self.assertEqual(paperwiki.report_slug("LatentMAS"), "latentmas")
self.assertEqual(paperwiki.report_slug("Graph of Agents: A Survey"), "graph-of-agents-a-survey")
self.assertEqual(paperwiki.report_paths(root, "LatentMAS")["report"], root / "reports/latentmas/report.md")
```

Add record-resolution tests proving sibling `record.json` wins over a legacy same-stem JSON, legacy JSON is accepted when `record.json` is absent, and missing-record lookup returns the canonical expected path for error reporting.

- [ ] **Step 3: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_paperwiki.PaperWikiTests.test_report_slug_and_paths tests.test_paperwiki.PaperWikiTests.test_record_path_prefers_canonical tests.test_paperwiki.PaperWikiTests.test_record_path_accepts_legacy -v`
Expected: failures because `report_slug`, `report_paths`, and `resolve_record_path` do not exist.

- [ ] **Step 4: Implement the minimal helpers**

In `paperwiki.py`, add:

```python
def report_slug(value):
    return slug(value)

def report_paths(root, value):
    folder = Path(root) / "reports" / report_slug(value)
    return {
        "folder": folder,
        "report": folder / "report.md",
        "html": folder / "report.html",
        "analysis": folder / "analysis.json",
        "record": folder / "record.json",
    }

def resolve_record_path(report, diagnose=False):
    report = Path(report)
    canonical = report.parent / "record.json"
    legacy = report.with_suffix(".json")
    if canonical.exists():
        if diagnose and legacy != canonical and legacy.exists():
            print(f"Using canonical reading record {canonical}; leaving legacy record {legacy} untouched", file=sys.stderr)
        return canonical
    return legacy if legacy.exists() else canonical
```

- [ ] **Step 5: Run focused and full tests (GREEN)**

Run: `python3 -m unittest tests.test_paperwiki -v`
Expected: all `PaperWikiTests` pass.

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

- [ ] **Step 6: Commit the helper contract**

```bash
git add paperwiki.py tests/test_paperwiki.py docs/superpowers/plans/2026-07-13-report-layout.md
git commit -m "test: define semantic report path contract"
```

## Task 2: Generate new reports in semantic directories

**Files:**
- Modify: `tests/test_paperwiki.py`
- Modify: `paperwiki.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing `read` command tests**

Use a temporary local PDF to avoid network calls. Add one test with `report_slug="LatentMAS"` and one with `report_slug=None`. Assert that explicit input creates `reports/latentmas/report.md` and `record.json`, while fallback uses the normalized local PDF title. Assert `reading.report_path` names the new `report.md`.

- [ ] **Step 2: Run the new tests and confirm RED**

Run: `python3 -m unittest tests.test_paperwiki.PaperWikiTests.test_read_uses_explicit_report_slug tests.test_paperwiki.PaperWikiTests.test_read_uses_title_slug_fallback -v`
Expected: failure because `cmd_read` still writes a flat paper-id filename.

- [ ] **Step 3: Implement nested generation and the CLI flag**

Change `cmd_read` to select `a.report_slug or p["title"]`, create the report directory, and write `report.md` plus `record.json`. Add:

```python
r.add_argument("--report-slug", help="Official paper abbreviation; defaults to a title-derived slug")
```

Keep raw PDF naming unchanged. Normalizing through `report_slug` prevents path traversal.

- [ ] **Step 4: Document the new command**

Update `README.md` examples and artifact layout to show `python3 paperwiki.py read ... --report-slug latentmas` and the semantic directory contract.

- [ ] **Step 5: Run focused and full tests (GREEN)**

Run: `python3 -m unittest tests.test_paperwiki -v`
Expected: all tests pass.

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

- [ ] **Step 6: Commit nested report generation**

```bash
git add paperwiki.py tests/test_paperwiki.py README.md
git commit -m "feat: generate semantic paper report directories"
```

## Task 3: Finalize canonical reports with legacy compatibility

**Files:**
- Modify: `tests/test_finalize.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Write failing canonical and precedence tests**

Add a canonical fixture at `reports/latentmas/{report.md,record.json}`. Assert finalize updates `record.json` and emits sibling `report.html`. Add a test with both `record.json` and `report.json` containing different titles; capture `stderr` and assert the canonical title is used plus the authoritative-record diagnostic appears.

- [ ] **Step 2: Run the new tests and confirm RED**

Run: `python3 -m unittest tests.test_finalize.FinalizeTests.test_uses_sibling_record_json tests.test_finalize.FinalizeTests.test_canonical_record_wins_with_diagnostic -v`
Expected: failure because finalize reads only `report.json`.

- [ ] **Step 3: Use the shared record resolver**

Replace `report.with_suffix(".json")` in `cmd_finalize` with `resolve_record_path(report, diagnose=True)`. Preserve the existing clear missing-record error and existing HTML generation behavior.

- [ ] **Step 4: Run finalize and full tests (GREEN)**

Run: `python3 -m unittest tests.test_finalize -v`
Expected: all finalize tests pass, including legacy fixtures.

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

- [ ] **Step 5: Commit finalize compatibility**

```bash
git add paperwiki.py tests/test_finalize.py
git commit -m "feat: finalize canonical report records"
```

## Task 4: Deposit nested reports with unambiguous Obsidian links

**Files:**
- Modify: `tests/test_deposit.py`
- Modify: `tests/test_paperwiki.py`
- Modify: `paperwiki.py`

- [ ] **Step 1: Write failing nested-deposit tests**

Create `reports/latentmas/{report.md,record.json}` under a temporary root and assert the paper page contains:

```text
[[reports/latentmas/report|Linked Paper report]]
```

Also retain tests for a legacy flat sidecar and record-free user-note deposit. Assert redeposit preserves the existing `## User notes` section.

- [ ] **Step 2: Run the new tests and confirm RED**

Run: `python3 -m unittest tests.test_deposit.DepositTests.test_nested_report_uses_vault_qualified_source_link tests.test_deposit.DepositTests.test_legacy_sidecar_still_deposits -v`
Expected: nested test fails because deposit reads only `report.json` and emits `[[report]]`.

- [ ] **Step 3: Implement record resolution and source-target derivation**

Use `resolve_record_path(src, diagnose=True)` in `cmd_deposit`. Add a helper that resolves `src` relative to `root`, strips `.md`, converts separators to `/`, and falls back to `src.stem` if the report is outside the vault. Render the alias as `<paper title> report`.

- [ ] **Step 4: Run deposit and full tests (GREEN)**

Run: `python3 -m unittest tests.test_deposit tests.test_paperwiki -v`
Expected: all deposit and integration tests pass.

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

- [ ] **Step 5: Commit nested deposit behavior**

```bash
git add paperwiki.py tests/test_deposit.py tests/test_paperwiki.py
git commit -m "feat: link nested reports from the wiki"
```

## Task 5: Version the canonical artifact contract and update workflow guidance

**Files:**
- Modify: `.gitignore`
- Modify: `tests/test_paperwiki.py`
- Modify: `docs/ACCEPTANCE.md`
- Modify: `docs/VALIDATION_MULTI_AGENT.md`
- Modify: `skills/read-paper/SKILL.md`
- Modify: `skills/deposit-paper-knowledge/SKILL.md`

- [ ] **Step 1: Write a failing Git ignore policy test**

In a temporary Git repository, copy the report-related ignore rules and assert `git check-ignore` does not ignore the four canonical files under `reports/latentmas/`, while `notes.tmp` remains ignored.

- [ ] **Step 2: Run the policy test and confirm RED**

Run: `python3 -m unittest tests.test_paperwiki.PaperWikiTests.test_gitignore_tracks_only_canonical_report_artifacts -v`
Expected: failure because `reports/*` ignores every artifact.

- [ ] **Step 3: Implement the approved ignore rules**

Replace the broad report ignore rule with:

```gitignore
reports/*
!reports/.gitkeep
!reports/*/
reports/*/*
!reports/*/report.md
!reports/*/report.html
!reports/*/analysis.json
!reports/*/record.json
```

- [ ] **Step 4: Update documentation and project skills**

Update acceptance/validation commands and both report workflow skills to use `reports/<official-abbreviation>/report.md`, `analysis.json`, and `record.json`. State that the abbreviation is preferred and title slug is the fallback.

- [ ] **Step 5: Run focused and full tests (GREEN)**

Run: `python3 -m unittest tests.test_paperwiki.PaperWikiTests.test_gitignore_tracks_only_canonical_report_artifacts -v`
Expected: pass.

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

- [ ] **Step 6: Commit artifact tracking and guidance**

```bash
git add .gitignore tests/test_paperwiki.py docs/ACCEPTANCE.md docs/VALIDATION_MULTI_AGENT.md skills/read-paper/SKILL.md skills/deposit-paper-knowledge/SKILL.md
git commit -m "docs: codify canonical report artifacts"
```

## Task 6: Migrate LatentMAS and Graph-of-Agents artifacts

**Files:**
- Add: `reports/latentmas/report.md`
- Add: `reports/latentmas/report.html`
- Add: `reports/latentmas/analysis.json`
- Add: `reports/latentmas/record.json`
- Add: `reports/goa/report.md`
- Add: `reports/goa/report.html`
- Add: `reports/goa/analysis.json`
- Add: `reports/goa/record.json`
- Modify: `wiki/papers/arxiv-2511-20639.md`
- Modify: `wiki/papers/arxiv-2604-17148.md`

- [ ] **Step 1: Preflight source and destination safety**

Verify all eight legacy source files exist and neither destination directory contains conflicting files. Do not touch `reports/latentmas-one-page-brief.md`.

- [ ] **Step 2: Move the eight canonical artifacts**

Move the LatentMAS files to `reports/latentmas/` and Graph-of-Agents files to `reports/goa/`, applying the approved semantic filenames. Use `mv` only after the preflight succeeds.

- [ ] **Step 3: Update records and Wiki links**

Change each `record.json` `reading.report_path` to its new `reports/<slug>/report.md` path. Update the Wiki paper source links to:

```text
[[reports/latentmas/report|LatentMAS report]]
[[reports/goa/report|Graph-of-Agents report]]
```

- [ ] **Step 4: Validate migrated data**

Run a Python JSON/read-path check that loads both records and verifies their referenced report exists. Run `git check-ignore -v` on all eight canonical artifacts and the one-page brief; canonical artifacts must be unignored and the brief must remain ignored.

- [ ] **Step 5: Run full tests and consistency checks**

Run: `python3 -m unittest discover -s tests -q`
Expected: all tests pass.

Run: `git diff --check`
Expected: no output.

- [ ] **Step 6: Commit the migrated reports**

```bash
git add reports/latentmas reports/goa wiki/papers/arxiv-2511-20639.md wiki/papers/arxiv-2604-17148.md
git commit -m "content: migrate reports to semantic directories"
```

## Task 7: Final verification and delivery to the existing PR

**Files:**
- Verify only; no planned modifications.

- [ ] **Step 1: Run the complete verification suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests pass without errors or failures.

Run: `git diff --check HEAD~6..HEAD`
Expected: no output.

- [ ] **Step 2: Inspect tracked and ignored scope**

Run: `git status --short`
Expected: only the pre-existing local `.obsidian/`, `wiki/.obsidian/`, and `tmp/` directories remain untracked.

Run: `git ls-files 'reports/*'`
Expected: `.gitkeep` plus four canonical files each for `latentmas` and `goa`; no one-page brief or temporary files.

- [ ] **Step 3: Push `dev`**

```bash
git push origin dev
```

Expected: `origin/dev` advances and the existing `dev → main` pull request updates automatically.
