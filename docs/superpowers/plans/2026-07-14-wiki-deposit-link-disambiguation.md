# Wiki Deposit Link Disambiguation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every deposited report and entity link resolvable in the Wiki, including cross-collection filename collisions, and synchronize canonical reports to `deposited` only after successful deposition.

**Architecture:** Keep `paperwiki.py` as the existing workflow boundary. Add a preflight collision map for all planned entity destinations, qualify only ambiguous wikilinks, and add a canonical-report finalization helper that updates report/record state after Wiki writes and rebuilds HTML from the updated Markdown.

**Tech Stack:** Python 3.9+, `unittest`, pathlib, JSON, Markdown renderer, Obsidian wikilinks.

---

## File map

- Modify `paperwiki.py`: collision discovery, link selection, canonical deposit-state synchronization.
- Modify `tests/test_deposit.py`: collision, status synchronization, and external-source immutability regressions.
- Regenerate `reports/{five-ws,moc,mars,agentmaster}/report.html` after status synchronization.
- Update `reports/{five-ws,moc,mars,agentmaster}/{report.md,record.json}` and generated Wiki/index/log artifacts through the CLI.

### Task 1: Disambiguate cross-collection entity links

**Files:**
- Modify: `tests/test_deposit.py`
- Modify: `paperwiki.py:333-356`

- [ ] **Step 1: Write the failing same-run collision test**

Add this test to `DepositTests`:

```python
def test_qualifies_same_stem_entities_across_collections(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        report = root / "reports/five-ws/report.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\npaper_id: arxiv:2602.11583\nstatus: reading\n"
            "human_confirmed: false\n---\n\n# Five Ws",
            encoding="utf-8",
        )
        record = {
            "paper_id": "arxiv:2602.11583",
            "title": "Five Ws",
            "reading": {
                "concepts": ["Emergent Language"],
                "methods": [],
                "datasets": [],
                "topics": ["Emergent Language"],
            },
        }
        (report.parent / "record.json").write_text(
            json.dumps(record), encoding="utf-8"
        )

        paperwiki.cmd_deposit(
            type("A", (), {"input": str(report), "root": str(root)})
        )

        page = (root / "wiki/papers/arxiv-2602-11583.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "[[wiki/concepts/emergent-language|Emergent Language]]", page
        )
        self.assertIn(
            "[[wiki/topics/emergent-language|Emergent Language]]", page
        )
        self.assertNotIn("- [[emergent-language|Emergent Language]]", page)
```

- [ ] **Step 2: Run the collision test and verify RED**

Run:

```bash
/tmp/paperwiki-python/bin/python -m unittest tests.test_deposit.DepositTests.test_qualifies_same_stem_entities_across_collections -v
```

Expected: FAIL because both links are currently `[[emergent-language|Emergent Language]]`.

- [ ] **Step 3: Implement collision-aware entity targets**

Add focused helpers near `link_entity`:

```python
def entity_path(root, collection, name):
    return root / "wiki" / collection / (slug(name) + ".md")

def colliding_entity_stems(root, entity_specs):
    destinations = {}
    for path in (root / "wiki").glob("*/*.md"):
        target = path.relative_to(root).with_suffix("").as_posix()
        destinations.setdefault(path.stem, set()).add(target)
    for collection, name in entity_specs:
        path = entity_path(root, collection, name)
        target = path.relative_to(root).with_suffix("").as_posix()
        destinations.setdefault(path.stem, set()).add(target)
    return {stem for stem, targets in destinations.items() if len(targets) > 1}

def entity_wikilink_target(root, target, colliding_stems):
    if target.stem in colliding_stems:
        return target.relative_to(root).with_suffix("").as_posix()
    return target.stem
```

Change `link_entity` to accept `colliding_stems`, use `entity_path`, and return:

```python
link_target = entity_wikilink_target(root, target, colliding_stems)
return f"[[{link_target}|{name}]]"
```

In `cmd_deposit`, first collect all `(collection, name)` pairs, compute `colliding_stems`, then call `link_entity` for each pair. This two-pass order is required so two entities created in the same deposit operation are recognized as a collision.

- [ ] **Step 4: Run deposit tests and verify GREEN**

Run:

```bash
/tmp/paperwiki-python/bin/python -m unittest tests.test_deposit -v
```

Expected: all deposit tests PASS, including the existing assertion that unique entities retain short links.

- [ ] **Step 5: Commit the isolated collision fix**

```bash
git add paperwiki.py tests/test_deposit.py
git commit -m "Disambiguate colliding wiki entity links"
```

### Task 2: Synchronize canonical deposit state

**Files:**
- Modify: `tests/test_deposit.py`
- Modify: `paperwiki.py:199-220,342-356`

- [ ] **Step 1: Write failing canonical and external-source tests**

Add a canonical test that creates `reports/sample/report.md` with `status: reading`, `human_confirmed: false`, and a sibling record with the same state. After `cmd_deposit`, assert:

```python
updated_record = json.loads((report.parent / "record.json").read_text())
updated_report = report.read_text(encoding="utf-8")
self.assertEqual(updated_record["status"], "deposited")
self.assertIn("status: deposited", updated_report.split("---", 2)[1])
self.assertIn("human_confirmed: false", updated_report.split("---", 2)[1])
self.assertTrue(report.with_suffix(".html").exists())
```

Extend `test_external_report_uses_explicit_path_instead_of_ambiguous_wikilink` by saving `original = report.read_text(...)` before deposition and asserting afterward:

```python
self.assertEqual(report.read_text(encoding="utf-8"), original)
self.assertFalse(report.with_suffix(".html").exists())
```

- [ ] **Step 2: Run both tests and verify RED**

Run:

```bash
/tmp/paperwiki-python/bin/python -m unittest \
  tests.test_deposit.DepositTests.test_canonical_deposit_synchronizes_source_status \
  tests.test_deposit.DepositTests.test_external_report_uses_explicit_path_instead_of_ambiguous_wikilink -v
```

Expected: canonical test FAILS because source status is still `reading`; external test already passes and protects its existing behavior.

- [ ] **Step 3: Add status and canonical-path helpers**

Add:

```python
def set_report_frontmatter_status(text, status):
    fields, body, had_frontmatter = split_report_frontmatter(text)
    if not had_frontmatter:
        raise ValueError("Canonical report is missing frontmatter")
    fields["status"] = status
    frontmatter = "---\n" + "\n".join(
        f"{key}: {value}" for key, value in fields.items()
    ) + "\n---\n"
    return frontmatter + body

def is_canonical_report(report, root, record, text, paper):
    try:
        relative = report.resolve().relative_to((root / "reports").resolve())
    except ValueError:
        return False
    fields, _, had_frontmatter = split_report_frontmatter(text)
    return (
        report.name == "report.md"
        and len(relative.parts) == 2
        and record.resolve() == (report.parent / "record.json").resolve()
        and had_frontmatter
        and fields.get("paper_id") == paper["paper_id"]
    )
```

- [ ] **Step 4: Finalize canonical state after Wiki writes**

At the end of `cmd_deposit`, after paper page, index, and log writes:

```python
if is_canonical_report(src, root, side, text, p):
    updated_report = set_report_frontmatter_status(text, "deposited")
    temporary_report = src.with_name(".report.deposit.md")
    temporary_html = src.with_name(".report.deposit.html")
    try:
        temporary_report.write_text(updated_report, encoding="utf-8")
        from scripts.render_report import render
        render(temporary_report, temporary_html)
        p["status"] = "deposited"
        src.write_text(updated_report, encoding="utf-8")
        side.write_text(
            json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary_html.replace(src.with_suffix(".html"))
    finally:
        temporary_report.unlink(missing_ok=True)
        temporary_html.unlink(missing_ok=True)
```

This renders the updated Markdown before committing source state and leaves external reports untouched.

- [ ] **Step 5: Run status and full deposit tests**

Run:

```bash
/tmp/paperwiki-python/bin/python -m unittest tests.test_deposit -v
```

Expected: all tests PASS; canonical status and HTML exist, external input is unchanged.

- [ ] **Step 6: Commit state synchronization**

```bash
git add paperwiki.py tests/test_deposit.py
git commit -m "Synchronize canonical wiki deposit state"
```

### Task 3: Regenerate and audit the repository Wiki

**Files:**
- Modify: `reports/five-ws/report.md`, `reports/five-ws/report.html`, `reports/five-ws/record.json`
- Modify: `reports/moc/report.md`, `reports/moc/report.html`, `reports/moc/record.json`
- Modify: `reports/mars/report.md`, `reports/mars/report.html`, `reports/mars/record.json`
- Modify: `reports/agentmaster/report.md`, `reports/agentmaster/report.html`, `reports/agentmaster/record.json`
- Modify/Create: `wiki/{papers,concepts,methods,datasets,topics}/*.md`, `index.md`, `log.md`

- [ ] **Step 1: Re-run the four canonical deposits sequentially**

```bash
python3 paperwiki.py deposit reports/five-ws/report.md --root .
python3 paperwiki.py deposit reports/moc/report.md --root .
python3 paperwiki.py deposit reports/mars/report.md --root .
python3 paperwiki.py deposit reports/agentmaster/report.md --root .
```

Expected: each command prints its single `wiki/papers/arxiv-*.md` target and exits zero.

- [ ] **Step 2: Run deterministic report formula verification**

```bash
/tmp/paperwiki-python/bin/python skills/read-paper/scripts/verify_report.py \
  reports/five-ws reports/moc reports/mars reports/agentmaster
```

Expected: 27, 73, 22, and 5 formulas respectively; every report has `status=ok`.

- [ ] **Step 3: Run a repository Wiki integrity audit**

Audit all six report records and assert:

- one `wiki/papers/<paper-id>.md` exists per record;
- the complete report body (excluding frontmatter) is embedded in its paper page;
- `[[reports/<slug>/report|...]]` exists;
- exactly one index link exists;
- every related-knowledge link resolves to exactly one path;
- every entity note links back to the paper;
- all six record and report statuses are `deposited`.

Expected output: `papers=6 index_links=6 wiki-audit=ok`.

- [ ] **Step 4: Run the complete regression suite and skill validator**

```bash
/tmp/paperwiki-python/bin/python -m unittest discover -s tests -v
/tmp/paperwiki-python/bin/python \
  /Users/shenshengzheng/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/read-paper
git diff --check
```

Expected: all tests PASS, `Skill is valid!`, and `git diff --check` exits zero.

- [ ] **Step 5: Commit generated Wiki and report state**

Stage only `index.md`, `log.md`, the four canonical report directories, and generated tracked/untracked Markdown under `wiki/concepts`, `wiki/methods`, `wiki/datasets`, `wiki/topics`, and `wiki/papers`. Explicitly exclude `.obsidian/`, `wiki/.obsidian/`, and `tmp/`.

```bash
git commit -m "Deposit multi-agent paper reports into wiki"
```

- [ ] **Step 6: Push the existing PR branch**

```bash
git push origin codex/five-ws-multi-agent-communication
```

Expected: remote branch advances and existing PR #3 includes all three implementation commits plus the design and plan commits.
