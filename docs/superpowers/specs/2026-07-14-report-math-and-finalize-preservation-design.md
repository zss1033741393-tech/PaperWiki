# Report Math Rendering and Finalize Preservation Design

## Context

The MOC, MARS, and AgentMaster deep-reading reports contain valid LaTeX formulas in Markdown, but the generated HTML sometimes displays partial raw source such as `sum` or `Phi`. The current renderer passes Markdown through Python Markdown before KaTeX sees it. Markdown processing can reinterpret characters inside math spans, so KaTeX receives damaged input.

The PR review also identified a separate data-flow problem. `paperwiki.py finalize` always replaces `report.md` with a short generated template. The deep-reading reports contain substantial authored analysis that is not represented in `analysis.json`; rerunning the documented command therefore destroys canonical content. The same bypass left the three new `record.json` files with noncanonical status values and a different shape from the finalized Five Ws record.

## Goals

- Render every inline and display formula without Markdown corrupting its LaTeX source.
- Detect malformed or unpaired math delimiters during tests.
- Preserve an existing deep-reading report byte-for-byte apart from normalized frontmatter when `finalize` is rerun.
- Keep initial placeholder reports compatible with the existing generated-template workflow.
- Use only status values produced by the application and keep unconfirmed analysis out of the `reviewed` state.
- Make canonical `record.json` files structurally consistent by embedding the complete analysis under `reading`.
- Rebuild and visually verify the four reports without changing their academic conclusions.

## Non-goals

- Making reports self-contained when CDN access is unavailable.
- Replacing KaTeX or Python Markdown.
- Moving long-form report prose into `analysis.json`.
- Automatically marking AI-generated analysis as human confirmed.
- Depositing reports into the wiki.

## Selected Architecture

### Math protection

`scripts/render_report.py` will protect math before Markdown conversion:

1. Scan fenced code blocks and math delimiters in a deterministic pass.
2. Replace valid `$...$` and `$$...$$` spans outside code with collision-resistant placeholders.
3. Run Python Markdown on the protected text.
4. Restore the exact HTML-escaped LaTeX source and delimiters.
5. Let the existing KaTeX auto-render script produce the final display.

Protection belongs at the renderer boundary rather than in individual reports. Editing formulas to accommodate Markdown would be fragile and would leave future reports exposed. The helper will reject or report unpaired delimiters in tests instead of silently producing broken HTML.

### Finalize preservation

`report.md` is the source of truth for long-form deep reading. `analysis.json` remains the structured summary used for indexing and metadata.

`finalize` will classify the report before writing:

- **Placeholder report:** the original `read` scaffold still contains the Paper Craft replacement instruction. `finalize` may replace it with the standard generated report.
- **Authored report:** the scaffold marker is absent and substantive content exists. `finalize` preserves the body and only normalizes the YAML frontmatter fields it owns.

In both cases, `finalize` will:

- validate and copy the canonical `analysis.json`;
- merge all analysis fields into `record.json["reading"]`;
- set `analysis_status` to `generated-awaiting-human-confirmation`;
- keep `status` as `reading` until an explicit human-confirmation workflow exists;
- render `report.html` through the shared report renderer;
- be idempotent when invoked repeatedly.

`finalize` will call the shared renderer as a Python function rather than invoke the vendored fallback generator, so manual rendering and `finalize` use one math-safe implementation.

### Frontmatter semantics

The application-owned fields will be:

- `paper_id`
- `status: reading`
- `source`
- `generated: true`
- `human_confirmed: false`

Here, `generated: true` means the artifact is maintained by the PaperWiki pipeline, not that every sentence came from a thin template. `human_confirmed: false` remains accurate until explicit confirmation. Existing additional metadata such as AgentMaster's venue will be preserved.

## Error Handling

- Missing analysis fields continue to raise `ValueError` before any report mutation.
- Malformed frontmatter raises a clear error instead of replacing the report.
- Math placeholders are restored before output is written; an internal count mismatch raises an error.
- Unpaired delimiters are covered by validation tests and reported with source context.
- HTML generation failure must not modify the preserved Markdown body.

## Test Strategy

Development follows red-green-refactor:

1. Add a renderer regression test containing subscripts, braces, `\sum`, `\Phi`, `\xrightarrow`, and a fenced code block with dollar signs. Confirm it fails against the current renderer.
2. Add a finalize regression test with unique authored prose and a formula. Confirm current finalize deletes it.
3. Add state/record tests requiring `reading`, `generated-awaiting-human-confirmation`, and full embedded analysis. Confirm current behavior fails.
4. Implement the smallest math-protection and preservation changes that pass each test.
5. Run all unit tests and `git diff --check`.
6. Rebuild Five Ws, MOC, MARS, and AgentMaster HTML files.
7. Scan generated HTML for raw broken math and use the in-app browser for visual checks at the reported MARS, MOC, and AgentMaster locations plus the remaining formulas.

## Migration of Existing Reports

Run the corrected `finalize` once for each of the four report directories. This will preserve long-form Markdown, normalize frontmatter and record state, embed each analysis, and regenerate HTML. The resulting artifact changes will be committed to the existing PR #3. Raw PDFs, temporary extraction files, and Obsidian state remain excluded.

## Acceptance Criteria

- The three user-reported formulas render completely, including `\sum`, `\Phi`, subscripts, braces, and the AgentMaster decomposition expression.
- No report HTML contains visible raw display delimiters or a formula damaged by Markdown emphasis processing.
- Rerunning `finalize` on an authored report retains a sentinel paragraph and all headings.
- Repeated finalize runs produce identical Markdown and record content.
- All four records use the same status vocabulary and embed the corresponding analysis.
- All repository tests pass and the four reports pass browser visual inspection.
