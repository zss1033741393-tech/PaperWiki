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
python paperwiki.py read https://arxiv.org/abs/2511.20639 --report-slug latentmas
python paperwiki.py finalize reports/latentmas/report.md reports/latentmas/analysis.json
python paperwiki.py deposit reports/latentmas/report.md
python paperwiki.py recommend --topic "agent memory"
python scripts/render_report.py reports/latentmas/report.md reports/latentmas/report.html
```

Each paper uses its official lowercase abbreviation under `reports/` (or a title-derived slug when no abbreviation is supplied). The versioned artifact contract is `report.md`, `report.html`, `analysis.json`, and `record.json` inside that directory.

Initialize submodules after cloning so the reading skill can invoke Paper Craft:

```powershell
git submodule update --init --recursive
```

Vendored integrations are pinned as Git submodules: Paper Craft, paper-search-mcp, InfraNodus skills, and Obsidian skills.

## Skills

- `discover-papers`: search, normalize, deduplicate, and transparently rank candidates.
- `read-paper`: create a structured learning report from a URL, DOI, arXiv ID, or PDF.
- `deposit-paper-knowledge`: ingest a report or notes into an idempotent linked knowledge base.

## Obsidian

The `wiki/` is an Obsidian vault: pages use short-name `[[wikilinks]]`, `[!summary]` callouts, and YAML properties, so opening the repo in Obsidian gives backlinks and graph view. The pinned `vendor/obsidian-skills` (kepano) adds optional companions — `obsidian-markdown`, `obsidian-cli`, `json-canvas`, `obsidian-bases`; see `skills/deposit-paper-knowledge/SKILL.md`.
