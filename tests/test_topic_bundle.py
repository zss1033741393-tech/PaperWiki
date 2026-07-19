"""Validation tests for topic syntheses backed by standalone source reports."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import paperwiki


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_standalone_report(root, slug, source_id, *, kind="source",
                            title="Source", source_type="blog",
                            url="https://example.com/source"):
    folder = root / "reports" / slug
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text(
        "---\n"
        f"paper_id: {source_id}\n"
        "status: deposited\n"
        f"source: {url}\n"
        "generated: true\n"
        "human_confirmed: false\n"
        "---\n\n"
        f"# {title}\n\n"
        "## 来源信息与阅读范围\n\nScope\n\n"
        "## 关键观点与证据\n\n- Claim [定位：全文 H2 #1，第 1 段]\n\n"
        "## 局限与适用边界\n\nLimits\n\n"
        "## 对 Agent Harness 主题的贡献\n\nContribution\n\n"
        "## User notes\n\n",
        encoding="utf-8",
    )
    (folder / "report.html").write_text("<html><body>rendered</body></html>\n", encoding="utf-8")
    analysis = {
        "research_question": "Question",
        "contributions": ["Contribution"],
        "method": "Argument analysis",
        "findings": ["Finding"],
        "limitations": ["Limit"],
        "concepts": ["Agent Harness"],
        "methods": ["Harness Decomposition"],
        "topics": ["Agent Harness"],
        "open_questions": ["Open question"],
        "evidence": ["全文 H2 #1，第 1 段"],
        "topic_contribution": "Contribution",
        "relations": [{"target": "other", "relation": "complements"}],
    }
    if kind == "paper":
        analysis.update({"experiments": [], "reproducibility": [], "datasets": []})
    (folder / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False), encoding="utf-8"
    )
    record = {
        "paper_id": source_id,
        "title": title,
        "kind": kind,
        "source_type": source_type,
        "source_url": url,
        "status": "deposited",
        "reading": analysis,
    }
    (folder / "record.json").write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return report


def _topic_source(report, source_id, *, kind="source", title="Source",
                  source_type="blog", url="https://example.com/source"):
    return {
        "source_id": source_id,
        "title": title,
        "url": url,
        "source_type": source_type,
        "role": "core",
        "status": "deposited",
        "report_path": report.relative_to(report.parents[2]).as_posix(),
        "report_kind": kind,
        "report_sha256": _sha256(report),
    }


def _seed_topic(root, sources):
    folder = root / "reports" / "topic-harness"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text(
        "---\ntopic_id: harness\nkind: topic\nstatus: deposited\n"
        "generated: true\nhuman_confirmed: false\n---\n\n"
        "# Agent Harness\n\n## 来源导航\n\nBody\n",
        encoding="utf-8",
    )
    (folder / "report.html").write_text("<html><body>topic</body></html>\n", encoding="utf-8")
    record = {
        "kind": "topic",
        "topic_slug": "harness",
        "title": "Agent Harness",
        "source_reports_required": True,
        "sources": sources,
        "entities": {},
    }
    (folder / "record.json").write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return report


class TopicBundleValidationTests(unittest.TestCase):
    def test_rejects_missing_standalone_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "reports" / "missing" / "report.md"
            source = {
                "source_id": "url:aaa111aaa111",
                "title": "Missing",
                "url": "https://example.com/missing",
                "source_type": "blog",
                "role": "core",
                "status": "deposited",
                "report_path": "reports/missing/report.md",
                "report_kind": "source",
                "report_sha256": "0" * 64,
            }
            topic = _seed_topic(root, [source])

            with self.assertRaisesRegex(ValueError, "Missing source report"):
                paperwiki.validate_topic_bundle(topic, root)
            self.assertFalse(missing.exists())

    def test_rejects_source_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_standalone_report(root, "one", "url:aaa111aaa111")
            source = _topic_source(report, "url:bbb222bbb222")
            topic = _seed_topic(root, [source])

            with self.assertRaisesRegex(ValueError, "Source identity mismatch"):
                paperwiki.validate_topic_bundle(topic, root)

    def test_rejects_duplicate_report_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_standalone_report(root, "one", "url:aaa111aaa111")
            one = _topic_source(report, "url:aaa111aaa111")
            two = dict(one, source_id="url:bbb222bbb222", title="Other")
            topic = _seed_topic(root, [one, two])

            with self.assertRaisesRegex(ValueError, "Duplicate source report path"):
                paperwiki.validate_topic_bundle(topic, root)

    def test_rejects_stale_report_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_standalone_report(root, "one", "url:aaa111aaa111")
            source = _topic_source(report, "url:aaa111aaa111")
            topic = _seed_topic(root, [source])
            report.write_text(report.read_text(encoding="utf-8") + "Changed\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Source report digest mismatch"):
                paperwiki.validate_topic_bundle(topic, root)

    def test_rejects_incomplete_canonical_artifact_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_standalone_report(root, "one", "url:aaa111aaa111")
            source = _topic_source(report, "url:aaa111aaa111")
            topic = _seed_topic(root, [source])
            report.with_suffix(".html").unlink()

            with self.assertRaisesRegex(ValueError, "Missing source artifact"):
                paperwiki.validate_topic_bundle(topic, root)

    def test_accepts_five_sources_and_one_paper(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sources = []
            for index in range(5):
                source_id = f"url:aaa111aaa11{index}"
                report = _seed_standalone_report(
                    root, f"source-{index}", source_id,
                    title=f"Source {index}", url=f"https://example.com/{index}"
                )
                sources.append(_topic_source(
                    report, source_id, title=f"Source {index}",
                    url=f"https://example.com/{index}"
                ))
            paper = _seed_standalone_report(
                root, "paper", "arxiv:2606.10106", kind="paper",
                title="Harness Conditions", source_type="paper",
                url="https://arxiv.org/abs/2606.10106",
            )
            sources.append(_topic_source(
                paper, "arxiv:2606.10106", kind="paper",
                title="Harness Conditions", source_type="paper",
                url="https://arxiv.org/abs/2606.10106",
            ))
            topic = _seed_topic(root, sources)

            result = paperwiki.validate_topic_bundle(topic, root)

            self.assertEqual(result["source_count"], 6)
            self.assertEqual(result["source_kinds"], {"source": 5, "paper": 1})


class TopicBundleDepositTests(unittest.TestCase):
    @staticmethod
    def _args(input_path, root):
        return type("Args", (), {"input": str(input_path), "root": str(root)})

    def test_mixed_bundle_links_source_and_paper_without_duplicate_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_report = _seed_standalone_report(
                root, "web", "url:aaa111aaa111", title="Web Source"
            )
            paper_report = _seed_standalone_report(
                root, "paper", "arxiv:2606.10106", kind="paper",
                title="Harness Conditions", source_type="paper",
                url="https://arxiv.org/abs/2606.10106",
            )
            sources = [
                _topic_source(source_report, "url:aaa111aaa111", title="Web Source"),
                _topic_source(
                    paper_report, "arxiv:2606.10106", kind="paper",
                    title="Harness Conditions", source_type="paper",
                    url="https://arxiv.org/abs/2606.10106",
                ),
            ]
            topic = _seed_topic(root, sources)
            paperwiki.cmd_deposit(self._args(source_report, root))
            paperwiki.cmd_deposit(self._args(paper_report, root))

            paperwiki.cmd_deposit(self._args(topic, root))

            source_page = root / "wiki/sources/url-aaa111aaa111.md"
            paper_page = root / "wiki/papers/arxiv-2606-10106.md"
            duplicate = root / "wiki/sources/arxiv-2606-10106.md"
            self.assertTrue(source_page.exists())
            self.assertTrue(paper_page.exists())
            self.assertFalse(duplicate.exists())
            self.assertEqual(source_page.read_text(encoding="utf-8").count("[[harness|Agent Harness]]"), 1)
            self.assertEqual(paper_page.read_text(encoding="utf-8").count("[[harness|Agent Harness]]"), 1)
            topic_page = (root / "wiki/topics/harness.md").read_text(encoding="utf-8")
            self.assertIn("[[url-aaa111aaa111|Web Source]]", topic_page)
            self.assertIn("[[arxiv-2606-10106|Harness Conditions]]", topic_page)

    def test_standalone_deposit_deduplicates_legacy_topic_backlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_report = _seed_standalone_report(
                root, "web", "url:aaa111aaa111", title="Web Source"
            )
            record_path = source_report.parent / "record.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["reading"]["concepts"] = ["Context Engineering"]
            record_path.write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            source_page = root / "wiki/sources/url-aaa111aaa111.md"
            source_page.parent.mkdir(parents=True)
            source_page.write_text(
                "# Web Source\n\n## Related pages\n\n"
                "- [[agent-harness|Agent Harness]]\n",
                encoding="utf-8",
            )

            paperwiki.cmd_deposit(self._args(source_report, root))

            text = source_page.read_text(encoding="utf-8")
            self.assertEqual(text.count("[[agent-harness|Agent Harness]]"), 1)

    def test_required_bundle_refuses_topic_deposit_before_source_pages_exist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_report = _seed_standalone_report(
                root, "web", "url:aaa111aaa111", title="Web Source"
            )
            topic = _seed_topic(
                root, [_topic_source(source_report, "url:aaa111aaa111", title="Web Source")]
            )

            with self.assertRaisesRegex(ValueError, "Deposit standalone report before topic"):
                paperwiki.cmd_deposit(self._args(topic, root))

            self.assertFalse((root / "wiki/sources/url-aaa111aaa111.md").exists())

    def test_redeposit_keeps_one_backlink_and_preserves_source_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_report = _seed_standalone_report(
                root, "web", "url:aaa111aaa111", title="Web Source"
            )
            topic = _seed_topic(
                root, [_topic_source(source_report, "url:aaa111aaa111", title="Web Source")]
            )
            args = self._args(source_report, root)
            paperwiki.cmd_deposit(args)
            source_page = root / "wiki/sources/url-aaa111aaa111.md"
            source_page.write_text(
                source_page.read_text(encoding="utf-8").replace(
                    "## User notes\n\n", "## User notes\n\nkeep this\n"
                ),
                encoding="utf-8",
            )

            paperwiki.cmd_deposit(self._args(topic, root))
            paperwiki.cmd_deposit(self._args(topic, root))

            text = source_page.read_text(encoding="utf-8")
            self.assertEqual(text.count("[[harness|Agent Harness]]"), 1)
            self.assertIn("keep this", text)


if __name__ == "__main__":
    unittest.main()
