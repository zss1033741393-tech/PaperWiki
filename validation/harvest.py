#!/usr/bin/env python3
"""Freeze real discovery output for the target multi-agent queries as reproducible fixtures.

Runs the real `discover` pipeline (arXiv, Semantic Scholar, Crossref, OpenAlex, Hugging Face)
and records, per query, how many papers survived, which providers failed, and the band split.
Provider intermittency is expected and captured — that is part of what we validate.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `paperwiki` imports
import paperwiki

QUERIES = ["LLM multi-agent collaboration", "multi-agent orchestration"]
OUT = Path(__file__).parent / "fixtures" / "discovery"


def run(query, limit=12, broader=False):
    out = OUT / (paperwiki.slug(query) + ".json")
    args = type("A", (), {"query": query, "limit": limit, "since_years": 1,
                          "no_huggingface": False, "broader": broader, "output": str(out)})
    paperwiki.cmd_discover(args)
    return out, json.loads(out.read_text(encoding="utf-8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"harvested_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "note": "provider errors are expected (IP-level rate limits); fault-tolerance keeps real results flowing",
                "runs": []}
    for q in QUERIES:
        out, payload = run(q)
        errs = {e["provider"]: (e.get("error") or "")[:60] for e in payload.get("errors", [])}
        bands = {}
        for p in payload["papers"]:
            b = p["discovery"]["band"]
            bands[b] = bands.get(b, 0) + 1
        provs = sorted({pr.get("provider") for p in payload["papers"] for pr in p.get("provenance", [])})
        manifest["runs"].append({"query": q, "fixture": out.name, "returned": len(payload["papers"]),
                                 "contributing_providers": provs, "provider_errors": errs, "bands": bands})
        print(f"{q!r}: {len(payload['papers'])} papers | providers={provs} | errors={list(errs)}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manifest written ->", OUT / "manifest.json")


if __name__ == "__main__":
    main()
