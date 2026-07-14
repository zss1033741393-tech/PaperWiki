#!/usr/bin/env python3
"""Verify that a rendered PaperWiki report preserves every Markdown formula."""

from __future__ import annotations

import argparse
import html
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.report_math import MATH_TOKEN, protect_math  # noqa: E402


def resolve_report(target: Path) -> tuple[Path, Path]:
    """Return the canonical Markdown and sibling HTML paths for a target."""
    markdown_path = target / "report.md" if target.is_dir() else target
    return markdown_path, markdown_path.with_suffix(".html")


def verify_report(target: Path) -> tuple[int, list[str], Path]:
    """Return formula count, validation errors, and the resolved Markdown path."""
    markdown_path, html_path = resolve_report(target)
    errors: list[str] = []

    if not markdown_path.is_file():
        return 0, [f"Markdown report not found: {markdown_path}"], markdown_path
    if not html_path.is_file():
        return 0, [f"Rendered report not found: {html_path}"], markdown_path

    markdown_text = markdown_path.read_text(encoding="utf-8")
    rendered_html = html_path.read_text(encoding="utf-8")
    try:
        _, formulas = protect_math(markdown_text)
    except ValueError as error:
        return 0, [str(error)], markdown_path

    expected_counts = Counter(html.escape(formula) for formula in formulas)
    first_formula_index = {
        escaped: index
        for index, escaped in reversed(list(enumerate(map(html.escape, formulas), start=1)))
    }
    for escaped, expected_count in expected_counts.items():
        actual_count = rendered_html.count(escaped)
        if actual_count < expected_count:
            index = first_formula_index[escaped]
            errors.append(
                f"formula {index} is missing or changed "
                f"(expected {expected_count}, found {actual_count})"
            )

    placeholder_prefix = MATH_TOKEN.split("{", 1)[0]
    if placeholder_prefix in rendered_html:
        errors.append("rendered HTML contains an unresolved math placeholder")

    return len(formulas), errors, markdown_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify exact formula preservation from report.md to report.html."
    )
    parser.add_argument(
        "reports",
        nargs="+",
        type=Path,
        help="report.md paths or directories containing report.md and report.html",
    )
    args = parser.parse_args(argv)

    failed = False
    for target in args.reports:
        formula_count, errors, markdown_path = verify_report(target)
        if errors:
            failed = True
            for error in errors:
                print(f"{markdown_path}: {error}", file=sys.stderr)
            continue
        print(f"{markdown_path}: formulas={formula_count} status=ok")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
