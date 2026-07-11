#!/usr/bin/env python3
"""Score normalized PaperWiki records from JSON stdin or a file."""

import argparse
import json
import sys

WEIGHTS = {
    "relevance": 0.30,
    "venue": 0.20,
    "citations": 0.15,
    "recency": 0.15,
    "reproducibility": 0.10,
    "author_continuity": 0.05,
    "novelty": 0.05,
}


def score(record):
    signals = record.get("discovery", {}).get("signals", {})
    available = {k: float(v) for k, v in signals.items() if k in WEIGHTS and v is not None}
    for key, value in available.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{key} must be between 0 and 1")
    coverage = sum(WEIGHTS[k] for k in available)
    total = sum(available[k] * WEIGHTS[k] for k in available) / coverage if coverage else None
    if total is None:
        band = "unranked"
    elif total >= 0.80 and coverage >= 0.70:
        band = "must-read"
    elif total >= 0.65:
        band = "recommended"
    elif total >= 0.50:
        band = "candidate"
    else:
        band = "watch"
    record.setdefault("discovery", {}).update({"score": total, "coverage": coverage, "band": band})
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="JSON file; omit to read stdin")
    args = parser.parse_args()
    stream = open(args.path, encoding="utf-8") if args.path else sys.stdin
    try:
        data = json.load(stream)
    finally:
        if args.path:
            stream.close()
    records = data if isinstance(data, list) else [data]
    json.dump([score(r) for r in records], sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()

