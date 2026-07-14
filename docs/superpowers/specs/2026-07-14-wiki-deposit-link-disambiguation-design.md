# Wiki Deposit Link Disambiguation Design

## Goal

Make deposited paper reports resolvable in the Obsidian knowledge graph even when two entity collections contain the same filename, and synchronize canonical report state only after deposition succeeds.

## Confirmed approach

Use collision-aware wikilinks:

- Keep the existing short form `[[stem|Alias]]` when a stem is unique across `wiki/`.
- When the same stem exists in more than one collection, use a vault-qualified link such as `[[wiki/concepts/emergent-language|Emergent Language]]` or `[[wiki/topics/emergent-language|Emergent Language]]`.
- Keep paper backlinks short because paper identity slugs are globally unique.

This preserves the current readable format while making the exceptional ambiguous case deterministic. It does not merge entities from different semantic collections.

## Deposit flow

1. Read the report and authoritative sibling `record.json`.
2. Create or update all entity notes and reciprocal paper backlinks.
3. Build paper-to-entity links after considering both existing Wiki stems and all entities in the current deposit operation, so same-run collisions are detected.
4. Write the paper page, index entry, and operation log.
5. For a canonical report under `<root>/reports/<slug>/report.md`, set `status: deposited` in both `record.json` and report frontmatter only after steps 1–4 succeed, then rebuild `report.html` from the report.
6. Preserve `human_confirmed: false` and the reading analysis status; deposited means archived in the Wiki, not human-reviewed.

External reports remain source inputs and are not modified.

## Failure behavior

- A failure before the final status synchronization leaves the canonical report in its previous state.
- Re-running deposit updates one paper page, does not duplicate entity backlinks or index entries, and may append a new operation-log event as an audit record.
- A collision never silently selects one collection.

## Verification

Automated tests must prove:

- Unique entities retain short wikilinks.
- Same-stem entities in different collections receive distinct vault-qualified links, including when both are created in one deposit call.
- Canonical report and record status become `deposited`, HTML is rebuilt, and human confirmation remains unchanged.
- External source reports are not modified.
- Existing deposition, report rendering, formula preservation, reciprocal-link, and idempotency tests remain green.

Repository-level audit must prove all six reports have one Wiki paper page, full report-body preservation, valid source links, unique index entries, resolvable related-knowledge links, and reciprocal backlinks.
