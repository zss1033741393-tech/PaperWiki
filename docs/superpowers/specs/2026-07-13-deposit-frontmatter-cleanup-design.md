# Deposit synthesis frontmatter cleanup design

Date: 2026-07-13
Status: Approved approach; implementation pending specification review

## Objective

Prevent a deposited paper report's YAML frontmatter from appearing inside the Wiki paper page's `Generated synthesis (draft)` section, and clean the same artifact from the existing LatentMAS and Graph-of-Agents pages.

## Selected approach

Sanitize the source report at the deposit synthesis boundary. A small helper removes only a leading YAML frontmatter block delimited by standalone `---` lines. `cmd_deposit` continues to use the original report text for metadata fallback and provenance, but embeds the sanitized text in the generated synthesis section.

This boundary is preferable to changing `finalize`, because canonical `report.md` files must retain their own YAML metadata. It is also safer than sanitizing the completed Wiki page, which could remove the Wiki page's own frontmatter.

## Parsing contract

The helper accepts Markdown text and returns Markdown text.

- If the document begins with an opening standalone `---` line and contains a matching closing standalone `---` line, remove that block and the immediately following blank line.
- Match both LF and CRLF line endings.
- Allow horizontal whitespace on delimiter lines.
- Do not remove `---` elsewhere in the document.
- If no complete leading frontmatter block exists, return the input unchanged.
- Preserve the report body text; trimming is limited to the boundary exposed by removing the frontmatter block.

## Deposit data flow

`cmd_deposit` reads the source once as the original text. Metadata resolution and the record-free title fallback continue to use that original text. Immediately before constructing the Wiki page body, it derives `synthesis_text` with the frontmatter helper and embeds only `synthesis_text` under `Generated synthesis (draft)`.

All other deposit behavior remains unchanged:

- canonical and legacy records resolve in the existing order;
- source-report references retain their vault-qualified or external-path representation;
- reciprocal entity links remain idempotent;
- existing `User notes` content is preserved;
- `index.md` and `log.md` retain their existing behavior.

## Existing content migration

Update only these generated pages:

- `wiki/papers/arxiv-2511-20639.md` (LatentMAS)
- `wiki/papers/arxiv-2604-17148.md` (Graph-of-Agents)

Inside each page, remove the embedded report YAML block that immediately follows `## Generated synthesis (draft)`. Do not re-run `deposit`, because that would append duplicate operation-log entries. Do not modify the page-level YAML frontmatter, source link, related knowledge links, synthesis prose, or user notes.

## Testing

Add deposit regression coverage proving:

1. a report's leading YAML frontmatter is absent from the generated synthesis;
2. the report body remains present;
3. an internal Markdown `---` separator remains present;
4. a report without frontmatter is unchanged in the synthesis;
5. redeposit continues to preserve existing user notes.

Repository verification includes the full unit-test suite, Python syntax compilation, `git diff --check`, and a content check that neither migrated generated-synthesis section begins with `---` while both Wiki pages retain their own top-level frontmatter.

## Delivery

Commit the behavior fix, tests, and two-page migration to the current `dev` branch, then push it to the existing `dev → main` pull request. Local `.obsidian/`, `wiki/.obsidian/`, and `tmp/` directories remain untouched and untracked.
