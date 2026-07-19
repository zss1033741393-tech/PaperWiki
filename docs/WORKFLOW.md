# Workflow Contract

| Intent | Skill | Required input | Output |
| --- | --- | --- | --- |
| Find papers | `discover-papers` | Topic | Ranked records |
| Track a curated list | `ingest-reading-list` | Awesome-list URL or README | `reading-lists/<slug>.json` + diff summary |
| Deep-read one source | `read-source` | URL, DOI, arXiv ID, PDF, repo, or record | Report and reading record |
| Study a topic | `study-topic` | Reading-list section or entry set | Chinese synthesis report + status writeback |
| Preserve knowledge | `deposit-paper-knowledge` | Report, synthesis, or notes | Linked wiki updates |

## Composition rules

- Use bibliographic metadata, provenance, and `paper_id` as the stable handoff contract.
- Treat `discovery`, `reading`, `user_notes`, and `knowledge` as optional sections.
- Do not auto-deposit after reading; allow personal conclusions first.
- Never make discovery a prerequisite for reading or reading a prerequisite for depositing existing notes.
- Record failures as recoverable state instead of dropping a paper.
- `study-topic` never auto-deposits; personal conclusions come first.
- `ingest-reading-list` re-runs refresh upstream metadata but never overwrite study states.
- Flagship deep reads are suggested by `study-topic` and triggered by the user, never automatically.

