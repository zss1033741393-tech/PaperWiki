"""L1 verification of curated-list ingestion: identity, classification, parsing, merge, CLI."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paperwiki

SAMPLE_README = """<div align="center"><h1>Awesome Harness Engineering</h1></div>

Intro paragraph.

## Contents

- [Foundations](#foundations)
- [Design Primitives](#design-primitives)

## Foundations

- [Harness Engineering](https://openai.com/index/harness-engineering/) — OpenAI's framing of the discipline.
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic's guide.

## Design Primitives

Text under the section head.

### Agent Loop

- [ReAct](https://arxiv.org/abs/2210.03629) — The foundational paper.
- [Harness Engineering](https://openai.com/index/harness-engineering/) — Duplicate URL listed again.
- [statewright](https://github.com/statewright/statewright) — State machine guardrails. ![Stars](https://img.shields.io/github/stars/statewright/statewright?style=flat-square)
- [broken entry without url
"""


class ParseAwesomeReadmeTests(unittest.TestCase):
    def test_parses_entries_with_sections_types_and_clean_descriptions(self):
        entries, unparsed = paperwiki.parse_awesome_readme(SAMPLE_README)
        by_title = {e["title"]: e for e in entries}
        self.assertEqual(len(entries), 4)  # duplicate URL folded into the first occurrence
        self.assertEqual(by_title["Harness Engineering"]["section_path"], ["Foundations"])
        self.assertEqual(by_title["Harness Engineering"]["also_in"], [["Design Primitives", "Agent Loop"]])
        self.assertEqual(by_title["ReAct"]["section_path"], ["Design Primitives", "Agent Loop"])
        self.assertEqual(by_title["ReAct"]["source_type"], "paper")
        self.assertEqual(by_title["ReAct"]["source_id"], "arxiv:2210.03629")
        self.assertEqual(by_title["statewright"]["source_type"], "github")
        self.assertNotIn("img.shields.io", by_title["statewright"]["description"])
        self.assertEqual(by_title["Building Effective Agents"]["description"], "Anthropic's guide.")

    def test_contents_section_is_skipped_and_bad_lines_reported(self):
        entries, unparsed = paperwiki.parse_awesome_readme(SAMPLE_README)
        self.assertFalse(any(e["section_path"] == ["Contents"] for e in entries))
        self.assertEqual(unparsed, ["- [broken entry without url"])

    def test_emoji_section_headers_are_normalized(self):
        entries, _ = paperwiki.parse_awesome_readme("## 📐 Foundations\n\n- [X](https://x.com/a) — d.\n")
        self.assertEqual(entries[0]["section_path"], ["Foundations"])


class UrlIdentityTests(unittest.TestCase):
    def test_norm_url_canonicalizes(self):
        self.assertEqual(
            paperwiki.norm_url("HTTP://Example.COM/Path/?utm_source=x&b=2#frag"),
            "https://example.com/Path?b=2",
        )

    def test_norm_url_equates_trailing_slash_and_scheme(self):
        a = paperwiki.norm_url("http://blog.langchain.com/post/")
        b = paperwiki.norm_url("https://blog.langchain.com/post")
        self.assertEqual(a, b)

    def test_url_source_id_prefers_arxiv_then_doi_then_hash(self):
        self.assertEqual(paperwiki.url_source_id("https://arxiv.org/abs/2210.03629v2"), "arxiv:2210.03629")
        self.assertEqual(paperwiki.url_source_id("https://doi.org/10.1145/AbC"), "doi:10.1145/abc")
        hashed = paperwiki.url_source_id("https://openai.com/index/harness-engineering/")
        self.assertTrue(hashed.startswith("url:"))
        self.assertEqual(len(hashed), len("url:") + 12)
        self.assertEqual(hashed, paperwiki.url_source_id("http://openai.com/index/harness-engineering"))

    def test_classify_source(self):
        cases = {
            "https://arxiv.org/abs/2210.03629": "paper",
            "https://doi.org/10.1145/x": "paper",
            "https://github.com/microsoft/TaskWeaver": "github",
            "https://github.blog/ai-and-ml/post/": "blog",
            "https://docs.anthropic.com/en/docs/x": "docs",
            "https://platform.claude.com/docs/x": "docs",
            "https://developers.openai.com/blog/x": "docs",
            "https://modelcontextprotocol.io/specification": "docs",
            "https://www.anthropic.com/engineering/x": "blog",
            "not-a-url": "other",
        }
        for url, expected in cases.items():
            self.assertEqual(paperwiki.classify_source(url), expected, url)


if __name__ == "__main__":
    unittest.main()
