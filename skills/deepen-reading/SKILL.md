---
name: deepen-reading
description: Use when the user wants to deepen or supplement an already-read PaperWiki report with PaperForge's complementary reading angles — reconstructing how the authors arrived at the idea, naming the one load-bearing assumption, sketching a cheap experiment that would test it, constructing the strongest counter-case, and proposing a non-incremental follow-up. This is a complementary reading pass, not a review/审稿 score.
---

# Deepen Reading

Read a paper the way `read-paper` did not. This skill is a **complementary reading channel**: `read-paper` produces the primary explanatory report; `deepen-reading` goes back over the same paper with PaperForge's reading lenses and adds the angles the first pass did not cover. It is "读它没想到的地方" — reading further, not grading the paper.

## Dependency

This skill applies the PaperForge active-reading framework, vendored at `vendor/paperforge/`:

- `vendor/paperforge/SKILL_CHN.md` — 12-section Chinese reading skill (default for this repo's Chinese reports).
- `vendor/paperforge/SKILL_EN.md` — English equivalent.

Read the matching-language file before writing. If `vendor/paperforge/` is absent, run `git submodule update --init vendor/paperforge` and report the missing dependency rather than reconstructing the framework from memory.

`read-paper` already covers PaperForge §1, §2, §4–§8 (problem, prior work, intuition, method, math, experiments, takeaways). This skill adds the reading angles a first pass usually skips — see `references/complementary-sections.md` for what to write and the survey adaptation. Do not restate what the report already says; add what it missed.

## Voice

Write like a person who just finished the paper and is thinking out loud, not like a form. Follow PaperForge's own style: concrete situation first, claim before evidence, plain words, every sentence carrying information, uncertainty kept visible. **Do not tag every sentence with 【推断】/【猜测】brackets** — that is the clinical AI voice PaperForge warns against. Keep source honesty in the prose instead: say "论文没明说，但……"、"更可能是……"、"这一步是猜测：……"、"这终究是重建，作者未必这么想". Distinguish four kinds of statement (paper states / prior work establishes / reasonable inference / speculation) by how you word them, not by prefix labels.

## Search discipline (do not skip)

PaperForge's §1/§3/§12 are not armchair sections — they require searching, not recall. Before writing:

- **Verify, don't assert.** Every named prior work in §3 (the reconstruction) — predecessor method, dataset, theoretical result — must be checked, not written from memory. Search arXiv/web and cite it (e.g. `arXiv:2412.06769`). If the environment's web tools are down, use the arXiv API directly (`curl -sL "https://export.arxiv.org/api/query?search_query=..."`) or the Semantic Scholar API; if nothing works, mark the anchor "unverified" rather than stating it as fact.
- **Calibrate follow-up novelty.** Before calling a §12 idea "non-incremental", search for it. The obvious follow-up to a paper is usually already published — find those 2–3 papers and either pivot to a genuinely open gap or state plainly that the direction is already being pursued (cite it). Do not manufacture novelty. Mark any residual "I didn't find prior work" as speculation, not a confirmed gap.
- **Supplement thin background.** Where §1/§2 context is missing for a claim to stand, add a sourced sentence, not a hand-wave.

## Workflow

1. Identify the target report directory `reports/<paper-slug>/`. Require an existing `report.md`, `analysis.json`, and `record.json`; if any is missing, run `read-paper` first.
2. Re-read the full `report.md` and `analysis.json`, and re-open the paper's full text (or the archived PDF under `raw/`) when an added claim needs page/section/figure evidence. Do not deepen from the summary alone.
3. Run the searches above: verify §3 anchors, calibrate the §12 follow-up against existing work, and collect the arXiv IDs / citations you will cite inline.
4. Write the complementary sections in `references/complementary-sections.md` in the voice above, grounded in the paper and in what the searches returned, citing page/section/figure/equation and arXiv IDs where it helps.
5. Style pass before finalizing: read the added prose once as an editor — no 【】tags, no "不是……而是" and similar low-information AI constructions, every sentence carries information, and the four source categories (paper states / prior work / inference / speculation) are distinguishable from the wording.
6. Append them to `report.md` as one delimited block under `## 精读补充（PaperForge 视角）`, placed **before** the trailing `## User notes`. Never overwrite existing report prose; this is additive.
7. Leave `analysis.json` as the machine-readable extraction. Add to its `open_questions` / `limitations` only when the deeper read genuinely surfaces a new one, and keep it terse and neutrally worded.
8. Rebuild HTML and re-sync the record: `python paperwiki.py finalize reports/<paper-slug>/report.md reports/<paper-slug>/analysis.json`. `finalize` preserves the authored body and only regenerates `report.html` + `record.json`.
   - **Already-deposited papers:** `finalize` unconditionally resets `status` to `reading` in both the frontmatter and `record.json`. If the target was `status: deposited`, restore `status: deposited` in both files afterward (the paper never left the wiki), or re-run `python paperwiki.py deposit reports/<paper-slug>/report.md` to refresh the wiki page. Do not silently leave a previously-deposited paper regressed to `reading`.

## Math must render in Obsidian, not just the HTML

The completion gate below (`verify_report.py`) only checks `report.html` (KaTeX). But this repo is also an **Obsidian vault**, and the user reads `report.md` in Obsidian, whose math parser is stricter. Inline `$...$` spans inside list items, and any `$...$` containing a bare `*` (e.g. `J^*`), can fail to parse in Obsidian Live Preview — the LaTeX then leaks as raw source and stray `*` collide with Markdown italics. Therefore, in added prose:

- Prefer prose and plain Unicode symbols (ΔJ, ε, κ, π) over inline LaTeX. Reuse a symbol the paper already defines and refer to formulas by name/location instead of re-typing them inline.
- If a formula genuinely needs LaTeX, put it in a display `$$...$$` block on its own line (Obsidian renders those reliably), never inline inside a bullet, and avoid bare `*` (write `^{*}` or say it in words).
- Verify both surfaces: `verify_report.py` for the HTML, and a browser/Obsidian spot-check that the added math actually renders.

## Non-method papers

For a survey, position paper, or benchmark, adapt rather than skip: the load-bearing assumption becomes the organizing one (is the taxonomy complete/mutually-exclusive, does the central recommendation generalize); the cheap experiment tests whether the framework earns its claim (e.g. inter-coder agreement on its own categories, or whether it predicts the design choices it says it explains); the counter-case is a real system the framework misclassifies. See `references/complementary-sections.md`.

## Completion Gate

Follow `AGENTS.md` and `read-paper`'s gate. Before claiming the supplement complete or committing:

1. Rebuild `report.html` from `report.md` via `finalize`; never hand-edit rendered HTML or formulas.
2. Run `python skills/read-paper/scripts/verify_report.py reports/<paper-slug>/report.md`. Any nonzero exit blocks completion.
3. Run the relevant regression tests, then the full suite.
4. Spot-check rendering in a browser (and Obsidian when available): no `.katex-error`, no leftover raw `$`, no stray italics from leaked math, no horizontal overflow the added content introduced.

Never set `reviewed` or `human_confirmed` without explicit human confirmation. A deeper read is still generated content awaiting human review.
