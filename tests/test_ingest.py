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


class MergeReadingListTests(unittest.TestCase):
    def _entry(self, sid, **kw):
        base = {"source_id": sid, "title": sid, "url": "https://x.com/" + sid,
                "source_type": "blog", "section_path": ["S"], "description": "d"}
        base.update(kw)
        return base

    def test_new_entries_start_unread_with_timestamps(self):
        merged, diff = paperwiki.merge_reading_list([], [self._entry("a")], "T1")
        self.assertEqual(diff, {"added": ["a"], "removed": [], "changed": []})
        self.assertEqual(merged[0]["status"], "unread")
        self.assertEqual(merged[0]["added_at"], "T1")
        self.assertEqual(merged[0]["status_updated_at"], "T1")

    def test_rerun_preserves_status_and_updates_metadata(self):
        old = [dict(self._entry("a"), status="studied", added_at="T0",
                    status_updated_at="T0", notes="mine")]
        new = [self._entry("a", title="Renamed", section_path=["S2"])]
        merged, diff = paperwiki.merge_reading_list(old, new, "T1")
        self.assertEqual(diff["changed"], ["a"])
        self.assertEqual(merged[0]["status"], "studied")
        self.assertEqual(merged[0]["added_at"], "T0")
        self.assertEqual(merged[0]["notes"], "mine")
        self.assertEqual(merged[0]["title"], "Renamed")
        self.assertEqual(merged[0]["section_path"], ["S2"])

    def test_upstream_removal_keeps_entry_flagged(self):
        old = [dict(self._entry("a"), status="unread", added_at="T0", status_updated_at="T0")]
        merged, diff = paperwiki.merge_reading_list(old, [], "T1")
        self.assertEqual(diff["removed"], ["a"])
        self.assertTrue(merged[0]["removed_upstream"])
        merged2, diff2 = paperwiki.merge_reading_list(merged, [], "T2")
        self.assertEqual(diff2["removed"], [])  # already flagged: not re-reported

    def test_reappearing_entry_clears_removed_flag(self):
        old = [dict(self._entry("a"), status="unread", added_at="T0",
                    status_updated_at="T0", removed_upstream=True)]
        merged, diff = paperwiki.merge_reading_list(old, [self._entry("a")], "T1")
        self.assertNotIn("removed_upstream", merged[0])
        self.assertEqual(diff, {"added": [], "removed": [], "changed": []})


class CmdIngestTests(unittest.TestCase):
    def _args(self, root, source, list_slug=None):
        return type("A", (), {"source": source, "list_slug": list_slug, "root": str(root)})

    def test_ingest_local_readme_writes_list_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            readme = root / "README.md"
            readme.write_text(SAMPLE_README, encoding="utf-8")

            paperwiki.cmd_ingest(self._args(root, str(readme), "harness-engineering"))

            out = root / "reading-lists/harness-engineering.json"
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["list_slug"], "harness-engineering")
            self.assertEqual(len(data["entries"]), 4)
            self.assertTrue(all(e["status"] == "unread" for e in data["entries"]))
            self.assertIn("retrieved_at", data)

    def test_ingest_rerun_is_idempotent_and_preserves_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            readme = root / "README.md"
            readme.write_text(SAMPLE_README, encoding="utf-8")
            args = self._args(root, str(readme), "hx")
            paperwiki.cmd_ingest(args)
            out = root / "reading-lists/hx.json"
            data = json.loads(out.read_text(encoding="utf-8"))
            data["entries"][0]["status"] = "studied"
            out.write_text(json.dumps(data), encoding="utf-8")

            paperwiki.cmd_ingest(args)

            again = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(again["entries"]), 4)
            self.assertEqual(again["entries"][0]["status"], "studied")

    def test_ingest_github_repo_url_fetches_raw_readme_and_derives_slug(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seen = {}

            def fake_fetch(url, binary=False):
                seen["url"] = url
                return SAMPLE_README

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_ingest(self._args(
                    root, "https://github.com/ai-boost/awesome-harness-engineering"))

            self.assertEqual(
                seen["url"],
                "https://raw.githubusercontent.com/ai-boost/awesome-harness-engineering/HEAD/README.md",
            )
            self.assertTrue((root / "reading-lists/awesome-harness-engineering.json").exists())

    def test_ingest_cli_is_wired(self):
        import subprocess, sys
        result = subprocess.run([sys.executable, "paperwiki.py", "ingest", "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--list-slug", result.stdout)

    def test_gitignore_tracks_curated_lists_but_not_transient_outputs(self):
        # Curated lists carry durable study state (like wiki pages); discover/recommend outputs stay transient.
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            source = Path(paperwiki.__file__).with_name(".gitignore")
            (root / ".gitignore").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            lists = root / "reading-lists"
            lists.mkdir()
            for name in ("harness-engineering.json", "latest.json", "recommended-next.json"):
                (lists / name).write_text("{}", encoding="utf-8")

            tracked = subprocess.run(["git", "check-ignore", "-q", "reading-lists/harness-engineering.json"], cwd=root)
            self.assertEqual(tracked.returncode, 1)
            for transient in ("latest.json", "recommended-next.json"):
                ignored = subprocess.run(["git", "check-ignore", "-q", f"reading-lists/{transient}"], cwd=root)
                self.assertEqual(ignored.returncode, 0, transient)


class MarkTests(unittest.TestCase):
    def _seed_list(self, root):
        lp = root / "reading-lists/hx.json"
        lp.parent.mkdir(parents=True)
        entries = [{"source_id": "url:aaa", "title": "A", "url": "https://x.com/a",
                    "source_type": "blog", "section_path": ["S"], "description": "",
                    "status": "unread", "added_at": "T0", "status_updated_at": "T0"}]
        lp.write_text(json.dumps({"list_slug": "hx", "source_repo": "r",
                                  "retrieved_at": "T0", "entries": entries}), encoding="utf-8")
        return lp

    def test_mark_updates_status_and_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            lp = self._seed_list(Path(td))
            hit = paperwiki.mark_list_entries(lp, {"url:aaa"}, "studied")
            self.assertEqual(hit, 1)
            entry = json.loads(lp.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "studied")
            self.assertNotEqual(entry["status_updated_at"], "T0")

    def test_blocked_requires_reason_and_records_it(self):
        with tempfile.TemporaryDirectory() as td:
            lp = self._seed_list(Path(td))
            with self.assertRaises(ValueError):
                paperwiki.mark_list_entries(lp, {"url:aaa"}, "blocked")
            paperwiki.mark_list_entries(lp, {"url:aaa"}, "blocked", reason="paywall")
            entry = json.loads(lp.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["blocked_reason"], "paywall")

    def test_invalid_status_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            lp = self._seed_list(Path(td))
            with self.assertRaises(ValueError):
                paperwiki.mark_list_entries(lp, {"url:aaa"}, "done")

    def test_reason_with_non_blocked_status_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            lp = self._seed_list(Path(td))
            with self.assertRaises(ValueError):
                paperwiki.mark_list_entries(lp, {"url:aaa"}, "studied", reason="oops")

    def test_unblocking_clears_blocked_reason(self):
        with tempfile.TemporaryDirectory() as td:
            lp = self._seed_list(Path(td))
            paperwiki.mark_list_entries(lp, {"url:aaa"}, "blocked", reason="paywall")
            paperwiki.mark_list_entries(lp, {"url:aaa"}, "queued")
            entry = json.loads(lp.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "queued")
            self.assertNotIn("blocked_reason", entry)

    def test_cmd_mark_resolves_slug_via_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_list(root)
            paperwiki.cmd_mark(type("A", (), {"list": "hx", "source_ids": ["url:aaa"],
                                              "status": "queued", "reason": None, "root": str(root)}))
            entry = json.loads((root / "reading-lists/hx.json").read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "queued")


if __name__ == "__main__":
    unittest.main()
