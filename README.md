# PaperWiki

PaperWiki is a composable workflow for discovering worthwhile papers, reading a selected paper, and depositing reviewed knowledge into a durable Markdown wiki.

```text
discover-papers -> read-source -> deposit-paper-knowledge
                      ^    \               ^
              URL/DOI/PDF/web  deepen-reading  existing report / notes
                               (PaperForge 精读补充)
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

`finalize` treats an already authored `report.md` as the source of truth for long-form analysis: it preserves the body, normalizes pipeline-owned frontmatter, embeds `analysis.json` into `record.json`, and rebuilds `report.html`. It only replaces the initial `read` scaffold while that scaffold still contains the Paper Craft placeholder. Unconfirmed analysis remains `status: reading` with `analysis_status: generated-awaiting-human-confirmation`; `reviewed` is reserved for an explicit human-confirmation workflow.

Initialize submodules after cloning so the reading skill can invoke Paper Craft:

```powershell
git submodule update --init --recursive
```

Vendored integrations are pinned as Git submodules: Paper Craft, paper-search-mcp, InfraNodus skills, Obsidian skills, and [PaperForge](https://github.com/FeijiangHan/PaperForge) (active-reading framework backing `deepen-reading`).

## Skills

- `discover-papers`: search, normalize, deduplicate, and transparently rank candidates.
- `read-source`: create a structured learning report from a URL, DOI, arXiv ID, PDF, web page, or repository.
- `deepen-reading`: a complementary reading pass over an already-read report, using PaperForge's angles the first pass skips — how the idea formed, the one load-bearing assumption, a one-week test of it, the strongest counter-case, and a non-incremental follow-up.
- `deposit-paper-knowledge`: ingest a report or notes into an idempotent linked knowledge base.

## Obsidian

The `wiki/` is an Obsidian vault: pages use short-name `[[wikilinks]]`, `[!summary]` callouts, and YAML properties, so opening the repo in Obsidian gives backlinks and graph view. The pinned `vendor/obsidian-skills` (kepano) adds optional companions — `obsidian-markdown`, `obsidian-cli`, `json-canvas`, `obsidian-bases`; see `skills/deposit-paper-knowledge/SKILL.md`.
