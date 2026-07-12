# PaperWiki

PaperWiki is a composable workflow for discovering worthwhile papers, reading a selected paper, and depositing reviewed knowledge into a durable Markdown wiki.

```text
discover-papers -> read-paper -> deposit-paper-knowledge
                      ^                    ^
                 URL / DOI / PDF      existing report / notes
```

Every stage is independently invocable. See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the implementation plan and [docs/WORKFLOW.md](docs/WORKFLOW.md) for the operating contract.

## Quick start

```powershell
python paperwiki.py discover "agent memory" --limit 10
python paperwiki.py read https://arxiv.org/abs/1706.03762
python paperwiki.py finalize reports/arxiv-1706-03762.md analysis.json
python paperwiki.py deposit reports/arxiv-1706-03762.md
python paperwiki.py recommend --topic "agent memory"
python scripts/render_report.py reports/arxiv-1706-03762.md reports/arxiv-1706-03762.html
```

Initialize submodules after cloning so the reading skill can invoke Paper Craft:

```powershell
git submodule update --init --recursive
```

Vendored integrations are pinned as Git submodules: Paper Craft, paper-search-mcp, InfraNodus skills, and Obsidian skills.

## Skills

- `discover-papers`: search, normalize, deduplicate, and transparently rank candidates.
- `read-paper`: create a structured learning report from a URL, DOI, arXiv ID, or PDF.
- `deposit-paper-knowledge`: ingest a report or notes into an idempotent linked knowledge base.
