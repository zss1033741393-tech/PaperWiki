# Acceptance Matrix

Run all offline checks with:

```powershell
python -m unittest discover -s tests -v
python -m py_compile paperwiki.py
```

Run the live workflow with:

```powershell
python paperwiki.py discover "agent memory" --limit 5
python paperwiki.py read https://arxiv.org/abs/1706.03762 --root <vault>
python paperwiki.py finalize <vault>/reports/arxiv-1706-03762.md examples/attention-is-all-you-need.analysis.json
python paperwiki.py deposit <vault>/reports/arxiv-1706-03762.md --root <vault>
python paperwiki.py recommend --topic "transformer architecture" --root <vault>
```

| Requirement | Evidence |
| --- | --- |
| Independent skills | Each CLI command and Skill accepts its own external input; optional record sections are not prerequisites. |
| Multi-source discovery | Live providers are arXiv, Semantic Scholar, and Crossref; provider failures are returned without discarding other results. paper-search-mcp is pinned for broader provider operation. |
| Explainable ranking | Every result includes signals, score, evidence coverage, band, and reasons. Missing signals are renormalized. |
| Stable identity | Unit tests cover DOI precedence, arXiv version normalization, and cross-provider merging. |
| Paper acquisition | Live test downloads the arXiv PDF; CLI accepts arXiv, DOI, direct PDF URL, and local PDF. DOI without an accessible PDF still creates a metadata-backed reading record. |
| Paper Craft report | `read-paper` routes analysis through pinned Paper Craft skills; `finalize` validates the structured analysis and creates Markdown plus styled HTML. |
| Human checkpoint | Generated reports are `human_confirmed: false`; deposit is a separate explicit command. |
| Idempotent knowledge | Tests run deposit twice, assert one paper page, and verify user notes survive. |
| Linked wiki | Tests verify paper-to-concept links and reciprocal concept-to-paper links; the same implementation handles methods, datasets, and topics. |
| Next reading | `recommend` derives a query from a requested or deposited topic and produces a scored reading list distinct from local page identities. |
| Recoverable failures | Discovery returns provider errors; command failures append JSONL events under `.paperwiki/errors.jsonl`. |

Semantic Scholar commonly rate-limits anonymous calls. Set `PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY` when operating the pinned paper-search-mcp integration at volume.
