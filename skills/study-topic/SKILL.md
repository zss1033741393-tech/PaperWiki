---
name: study-topic
description: Use when the user asks to study, survey, or synthesize a topic from a PaperWiki reading list or an ad-hoc source set, producing standalone reports for every selected source before one Chinese cross-source synthesis.
---

# Study Topic

## Required output model

A completed topic study is a report bundle, not one large summary:

1. One canonical standalone report for every selected source.
2. One topic synthesis that compares and connects those reports.
3. One topic record that binds source identity, report path, report kind, and report SHA-256.

Do not treat standalone reports as an optional flagship follow-up. If a selected source cannot be read, mark it `blocked` with the reason and keep the topic incomplete; never substitute a thin source stub for a required report.

## Workflow

1. Accept a reading-list section or a hand-picked set. Confirm scope when it contains more than about ten entries.
2. Select 5–8 core sources: foundational definitions first, then representative architecture, runtime, engineering, and empirical perspectives. Record selection roles and explicit exclusions.
3. For each selected source, follow `skills/read-source/SKILL.md` and create the canonical four-file set under `reports/<source-slug>/`: `report.md`, `report.html`, `analysis.json`, and `record.json`.
4. Verify each standalone report before starting synthesis. A report must contain deterministic evidence locators, limitations, `topic_contribution`, and `relations` to other selected sources.
5. Write the Chinese synthesis to `reports/topic-<slug>/report.md`. It must focus on topic definition, cross-source agreements and disagreements, pattern comparison, concept map, practical case, open questions, and a source-report navigation section. Do not repeat each standalone report in full.
6. Topic frontmatter: `topic_id`, `kind: topic`, `list_slug`, `sources`, `status`, `generated: true`, `human_confirmed: false`.
7. Write `record.json` with `source_reports_required: true`. Every `sources[]` item must include `source_id`, title, URL, source type, role, status, `report_path`, `report_kind`, and `report_sha256`.
8. Render topic HTML from Markdown with `python scripts/render_report.py <report.md> <report.html>`.
9. Run `python paperwiki.py validate-topic <topic-report.md> --root .`. Any nonzero result blocks deposit.
10. Deposit standalone reports first, then deposit the topic report. Do not auto-deposit before all report and bundle gates pass.

## Standalone report contract

Each report must include:

- source information and reading scope;
- problem and background;
- argument structure;
- at least three key claims with deterministic locators;
- concepts and methods;
- limitations and applicability boundaries;
- contribution to the topic;
- relationships to other selected sources;
- `## User notes`.

Blogs and docs cite document-absolute H2 order plus paragraph/list/table positions. Repositories cite paths and symbols. Papers cite sections, figures, tables, and PDF pages. Separate source claims, synthesis, and open inference explicitly.

## Topic synthesis contract

The synthesis keeps source-specific prose short: role, report link, unique contribution, and only the primary locator needed for the cross-source claim. It must contain at least:

- three cross-source agreements;
- two boundary or terminology differences;
- one complementary relationship;
- one concept map;
- one minimal practical comparison.

Facts remain traceable to the original source even when the synthesis links through a standalone report.

## Completion gate

Before claiming completion:

1. Rebuild all changed HTML from matching Markdown.
2. Run `python skills/read-source/scripts/verify_report.py <report.md>` for every changed report.
3. Run `python paperwiki.py validate-topic <topic-report.md> --root .`.
4. Run focused regressions, then the full test suite.
5. In a browser, check representative source, paper, and synthesis pages for Mermaid rendering, `.katex-error`, visible raw `$$`, and horizontal overflow.
6. Repeat deposit and prove material artifacts are byte-identical except for truthful operation-log entries.

Never set `reviewed` or `human_confirmed: true` without explicit human confirmation.
