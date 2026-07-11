# Multi-Agent Paper Validation

Validation query: `LLM multi-agent systems`, two-year window, ten results.

The first run exposed score saturation when Semantic Scholar anonymous requests were rate-limited and all exact-title matches had only relevance and recency evidence. The implementation was corrected by:

- adding OpenAlex as an impact/venue provider;
- merging DOI-bearing and arXiv-only records through identifier aliases;
- confidence-adjusting final scores by evidence coverage;
- enriching arXiv records with Hugging Face Paper Pages upvotes, linked GitHub repositories, project pages, and AI summaries;
- treating Hugging Face upvotes as logarithmically normalized community interest, not academic quality.

The selected paper was arXiv `2604.03295`, *Scaling Teams or Scaling Time? Memory Enabled Lifelong Learning in LLM Multi-Agent Systems*. Hugging Face supplied 10 upvotes and a linked code repository. The 21-page PDF was downloaded, text-extracted, visually inspected, finalized into Markdown/HTML, and deposited into the linked wiki.

This validation is intentionally reproducible through:

```powershell
python paperwiki.py discover "LLM multi-agent systems" --limit 10 --since-years 2
python paperwiki.py read https://arxiv.org/abs/2604.03295 --root <vault>
python paperwiki.py finalize <vault>/reports/arxiv-2604-03295.md examples/scaling-teams-or-scaling-time.analysis.json
python paperwiki.py deposit <vault>/reports/arxiv-2604-03295.md --root <vault>
```
