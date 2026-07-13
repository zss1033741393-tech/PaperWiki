# Paper report directory layout design

Date: 2026-07-13
Status: Approved and implemented on `dev`

## Objective

Organize generated paper reports by official paper abbreviation, track the useful report artifacts in Git, and keep PaperWiki's read, finalize, deposit, and Obsidian workflows consistent with the new layout.

## Directory convention

Each paper owns one directory under `reports/`:

```text
reports/
├── <official-abbreviation>/
│   ├── report.md
│   ├── report.html
│   ├── analysis.json
│   └── record.json
```

Directory names use the paper's official abbreviation, normalized to a lowercase ASCII slug. Examples:

```text
reports/latentmas/
reports/goa/
```

If a paper has no official abbreviation, use a concise normalized title slug. The workflow may accept an explicit report slug; otherwise it falls back to a title-derived slug.

## Artifact roles

- `report.md`: canonical editable deep-reading report.
- `report.html`: rendered reading version of `report.md`.
- `analysis.json`: structured paper analysis matching the read-paper analysis schema.
- `record.json`: PaperWiki paper record, provenance, reading state, and knowledge metadata.

All four artifact types are tracked by Git. Temporary extraction files, rendered PDF pages, downloaded sources, and other undeclared report-directory files remain ignored.

## Git ignore policy

The repository will unignore only the four semantic report filenames inside paper subdirectories:

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

This avoids unintentionally tracking temporary files while making the versioned report contract explicit.

## CLI behavior

### Read

`paperwiki.py read` creates the paper report directory and writes `report.md` plus `record.json`. It accepts `--report-slug <official-abbreviation>` for an explicit official abbreviation. Without that option, it derives a concise title slug.

### Finalize

`paperwiki.py finalize <report.md> <analysis.json>` reads the sibling `record.json`, updates the record, writes the finalized `report.md`, and generates sibling `report.html`.

### Deposit

`paperwiki.py deposit <report.md>` reads sibling `record.json`, deposits or updates the distilled page under `wiki/papers/`, and creates reciprocal knowledge links as before.

### Backward compatibility

Record resolution follows this order:

1. sibling `record.json`;
2. legacy same-stem JSON, such as `arxiv-2511-20639.json` or `report.json`.

Legacy flat reports remain readable during migration, but all newly generated reports use the nested semantic layout. If both formats exist beside one report, `record.json` is authoritative and the legacy sidecar is left untouched with a diagnostic warning.

## Obsidian links

Because many paper directories contain a file named `report.md`, short-name `[[report]]` links are ambiguous. Wiki paper pages therefore use vault-qualified source links:

```text
[[reports/latentmas/report|LatentMAS report]]
[[reports/goa/report|Graph-of-Agents report]]
```

Concept, method, dataset, and topic relations continue using short-name wikilinks because those note names remain globally unique.

## Migration

The current artifacts move as follows:

```text
reports/arxiv-2511-20639.md            -> reports/latentmas/report.md
reports/arxiv-2511-20639.html          -> reports/latentmas/report.html
reports/arxiv-2511-20639.analysis.json -> reports/latentmas/analysis.json
reports/arxiv-2511-20639.json          -> reports/latentmas/record.json

reports/arxiv-2604-17148.md            -> reports/goa/report.md
reports/arxiv-2604-17148.html          -> reports/goa/report.html
reports/arxiv-2604-17148.analysis.json -> reports/goa/analysis.json
reports/arxiv-2604-17148.json          -> reports/goa/record.json
```

The LatentMAS one-page brief is not one of the four canonical artifacts. It remains ignored until a separate poster/brief artifact convention is approved.

Each migrated `record.json` updates `reading.report_path`. Wiki source-report links are updated to their vault-qualified paths. Existing distilled paper filenames and entity backlinks do not change.

## Error handling

- Finalize fails with a clear error if neither `record.json` nor a legacy sidecar exists. Deposit retains its existing user-notes fallback when no record is available.
- Explicit report slugs are normalized and must not resolve outside `reports/`.
- A migration must not overwrite an existing destination directory with conflicting content.
- When both new and legacy record files exist, the command reports that `record.json` is authoritative instead of silently merging inconsistent metadata.

## Validation

Automated tests cover:

- new nested report generation;
- explicit abbreviation and title-slug fallback;
- `record.json` resolution;
- legacy sidecar compatibility;
- finalize output at `report.html`;
- deposit from nested reports;
- vault-qualified Obsidian source links;
- `.gitignore` inclusion of the four canonical artifacts and exclusion of undeclared files;
- idempotent deposit and preservation of user notes.

Repository-level verification includes the full unit test suite, `git diff --check`, report-record path validation, and reciprocal Wiki-link validation.

## Delivery

Implementation will be committed to the existing `dev` branch and pushed to the open `dev → main` pull request. Local `.obsidian/`, `wiki/.obsidian/`, and `tmp/` content remain outside the change.
