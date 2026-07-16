"""L1 verification of curated-list ingestion: identity, classification, parsing, merge, CLI."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paperwiki


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
