# PaperWiki

PaperWiki is a composable workflow for discovering worthwhile papers, reading a selected paper, and depositing reviewed knowledge into a durable Markdown wiki.

```text
discover-papers -> read-paper -> deposit-paper-knowledge
                      ^                    ^
                 URL / DOI / PDF      existing report / notes
```

Every stage is independently invocable. See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the implementation plan and [docs/WORKFLOW.md](docs/WORKFLOW.md) for the operating contract.

## Skills

- `discover-papers`: search, normalize, deduplicate, and transparently rank candidates.
- `read-paper`: create a structured learning report from a URL, DOI, arXiv ID, or PDF.
- `deposit-paper-knowledge`: ingest a report or notes into an idempotent linked knowledge base.

