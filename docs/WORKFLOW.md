# Workflow Contract

| Intent | Skill | Required input | Output |
| --- | --- | --- | --- |
| Find papers | `discover-papers` | Topic | Ranked records |
| Deep-read | `read-source` | URL, DOI, arXiv ID, PDF, or record | Report and reading record |
| Preserve knowledge | `deposit-paper-knowledge` | Report or notes | Linked wiki updates |

## Composition rules

- Use bibliographic metadata, provenance, and `paper_id` as the stable handoff contract.
- Treat `discovery`, `reading`, `user_notes`, and `knowledge` as optional sections.
- Do not auto-deposit after reading; allow personal conclusions first.
- Never make discovery a prerequisite for reading or reading a prerequisite for depositing existing notes.
- Record failures as recoverable state instead of dropping a paper.

