---
name: study-topic
description: Use when the user asks to study, learn, survey, or synthesize a topic from a PaperWiki reading list (for example a section of an awesome list) or an ad-hoc set of sources, producing one Chinese synthesis report across several sources.
---

# Study Topic

## Workflow

1. Accept a reading-list section (e.g. "Context Delivery & Compaction" in `reading-lists/harness-engineering.json`) or a hand-picked set of entries. Confirm scope with the user when the section holds more than ~10 entries.
2. Select 5–8 core sources: foundational essays first, then one representative per `source_type`. Record the selection rationale in the report; list what was deliberately left out.
3. Fetch and read each source (GitHub repos to README + docs depth). Keep source claims and personal interpretation in separate sentences; never invent content. A source that cannot be fetched is marked `blocked` with a reason via `python paperwiki.py mark <list> <source_id> --status blocked --reason <why>`, and the synthesis states the evidence gap.
4. Write the Chinese synthesis to `reports/topic-<slug>/report.md` with sections: 主题界定 → 核心问题 → 模式对比 → 各来源观点与证据 → 工具盘点 → 开放问题与实践启发 → 来源清单. Follow Obsidian-safe conventions: no inline `$` math inside list items, no bare `*`, no 【】 source tags.
5. Report frontmatter: `topic_id`, `kind: topic`, `list_slug`, `sources` (source_id list), `status`, `generated: true`, `human_confirmed: false`.
6. Write `record.json` beside the report: `{kind: "topic", topic_slug, title, list_slug, sources: [{source_id, title, url, source_type, role: core|flagship|referenced, status}], entities: {concepts, methods, tools}, created, updated}`. Topic reports do NOT get an `analysis.json` and do NOT run `finalize`; render HTML with `python scripts/render_report.py reports/topic-<slug>/report.md reports/topic-<slug>/report.html` when asked.
7. Mark studied entries: `python paperwiki.py mark <list> <source_id ...> --status studied`.
8. When a flagship source deserves a standalone deep read, recommend `read-source` for it — do not run it automatically, and do not auto-deposit.

## Guardrails

- Separate 来源观点 from 我的解读 in every synthesis section.
- Cite locators: section/heading for blogs and docs, file paths for repos, page/figure for papers.
- Record failures as recoverable state; a blocked source never silently disappears from the 来源清单.
