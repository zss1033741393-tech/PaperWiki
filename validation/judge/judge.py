#!/usr/bin/env python3
"""L3 LLM-as-judge for reading taste (and discovery relevance).

If ANTHROPIC_API_KEY is set, scores an analysis JSON against a rubric via the
Anthropic Messages API (stdlib urllib, no SDK). Otherwise it writes the judging
prompt and exits, so scoring can be done by an in-session / subagent judge
(this session used an independent Claude subagent — see validation/judge/scores/).
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

DIMENSIONS = {
    "faithfulness": "Every claim/number in the analysis is traceable to the source paper; nothing fabricated.",
    "insight": "tldr, contributions, and open_questions show genuine understanding, not filler.",
    "completeness": "All sections are substantively filled, not placeholder.",
}

PROMPT_TMPL = """You are an adversarial reviewer. Given a structured analysis of a paper,
score each dimension 1-5 (5=excellent) and justify in one sentence. Actively hunt for
hallucinated numbers or unsupported claims and list them under "violations".
Return ONLY JSON: {{"scores":{{"faithfulness":{{"score":N,"rationale":"..."}},...}},"violations":[...]}}.

Dimensions:
{dims}

Analysis under review:
{analysis}
"""


def call_anthropic(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = json.dumps({
        "model": "claude-sonnet-5", "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["content"][0]["text"]


def main():
    analysis_path = sys.argv[1] if len(sys.argv) > 1 else "validation/fixtures/reading/2605-14483.analysis.json"
    analysis = Path(analysis_path).read_text(encoding="utf-8")
    prompt = PROMPT_TMPL.format(dims=json.dumps(DIMENSIONS, ensure_ascii=False), analysis=analysis)
    stem = Path(analysis_path).stem
    scores_dir = Path("validation/judge/scores")
    prompts_dir = Path("validation/judge/prompts")
    scores_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    out = call_anthropic(prompt)
    if out is None:
        (prompts_dir / f"{stem}.txt").write_text(prompt, encoding="utf-8")
        print(f"ANTHROPIC_API_KEY not set -> prompt written to {prompts_dir/f'{stem}.txt'}")
        print("Run the in-session / subagent judge; store result in", scores_dir / f"{stem}.json")
        return
    (scores_dir / f"{stem}.json").write_text(out, encoding="utf-8")
    print("wrote", scores_dir / f"{stem}.json")


if __name__ == "__main__":
    main()
