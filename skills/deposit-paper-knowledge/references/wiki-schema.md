# Wiki schema

Use `raw/papers/` for immutable sources, `reports/` for complete reports, and `wiki/` for distilled pages.

Required collections are `papers`, `concepts`, `methods`, `datasets`, and `topics`; `authors`, `sources`, and `tools` are optional. `sources` holds non-paper source pages (frontmatter: `title`, `type: source`, `source_type`, `url`, `source_id`). `tools` holds framework/tool pages (frontmatter: `title`, `type: tool`) describing the tool's role in a harness. Harness design patterns (compaction, hooks, plan-and-execute, ...) live in `methods`. Identity keys extend the paper rule with `url:<sha256-12>` for non-paper sources; the record field name stays `paper_id` for backward compatibility. Use stable lowercase slugs and readable frontmatter titles. Relationships use short-name Obsidian `[[stem|Alias]]` links when the stem is unique; when two collections contain the same stem, use a vault-qualified target such as `[[wiki/topics/agent-harness|Agent Harness]]`. Prefer ASCII entity names so filenames stay readable.

Each paper page contains bibliographic metadata, provenance, takeaway, research question, contributions, method, evidence, limitations, reproducibility, related pages, user notes, and update history. Mark generated drafts and human-confirmed content separately.

Topic pages built from a topic synthesis contain: `Synthesis report` (vault-qualified link to the Chinese report), `Sources`, `Related knowledge`, optionally `Related papers` (preserved from entity-created pages), and `User notes`. Generated relationship sections are inserted before the trailing `User notes` section. Entity pages created by topic or source deposits use `Related pages`; paper deposits use `Related papers`. An entity referenced by both source and paper deposits can intentionally contain both sections because they preserve the provenance kind of each backlink.

