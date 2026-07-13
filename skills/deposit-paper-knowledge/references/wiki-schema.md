# Wiki schema

Use `raw/papers/` for immutable sources, `reports/` for complete reports, and `wiki/` for distilled pages.

Required collections are `papers`, `concepts`, `methods`, `datasets`, and `topics`; `authors` is optional. Use stable lowercase slugs for filenames, readable frontmatter titles, and **short-name** Obsidian `[[stem|Alias]]` wikilinks (Obsidian's default shortest-path form, resolved by note name across the vault) for relationships. Prefer ASCII entity names so filenames stay readable.

Each paper page contains bibliographic metadata, provenance, takeaway, research question, contributions, method, evidence, limitations, reproducibility, related pages, user notes, and update history. Mark generated drafts and human-confirmed content separately.

