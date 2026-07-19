# Curated List 学习流 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 PaperWiki 能从 awesome-harness-engineering 这类 curated list 摄取清单、按主题综述研读非论文来源，并沉淀到 wiki（spec：`docs/superpowers/specs/2026-07-16-harness-learning-design.md`）。

**Architecture:** 在 `paperwiki.py`（stdlib-only 单文件 CLI，全部实现都加在这个文件里，遵循其单行/分号密集风格）新增 `ingest`/`mark` 子命令与 URL 身份助手；泛化 `read`/`finalize`/`deposit` 以支持 `kind: source|topic` 记录；skills 层新增 `ingest-reading-list`、`study-topic`，将 `read-paper` 改名为 `read-source`。

**Tech Stack:** Python 3.12 stdlib（urllib/re/json/hashlib），unittest（CI 命令：`python -m unittest discover -s tests -v`），Obsidian Markdown。

**约定（每个任务都适用）：**
- 所有命令在仓库根目录执行（`import paperwiki` 依赖 cwd）。
- 测试风格：`unittest` + `tempfile.TemporaryDirectory` + `type("A", (), {...})` 参数对象；需要断网测试时用 `unittest.mock.patch.object(paperwiki, "fetch", fake)`。
- 不引入任何第三方依赖。
- 记录字段沿用 `paper_id` 作为身份字段名（值扩展出 `url:` 前缀方案），新增 `kind`（缺省=paper）与 `source_type` 字段。

**File Structure（全量清单）：**

| 动作 | 路径 | 职责 |
| --- | --- | --- |
| Modify | `paperwiki.py` | 身份助手、README 解析、清单 merge、`cmd_ingest`/`cmd_mark`、`cmd_read`/`cmd_finalize`/`cmd_deposit` 泛化、CLI 接线 |
| Create | `tests/test_ingest.py` | 身份/判型/解析/merge/ingest/mark 测试 |
| Create | `tests/test_read_source.py` | `cmd_read` 的 github/web 分支测试 |
| Create | `tests/test_deposit_kinds.py` | `kind: source/topic` 沉淀测试 |
| Modify | `tests/test_finalize.py` | source 记录的条件校验测试 |
| Create | `skills/ingest-reading-list/SKILL.md` + `references/reading-list.schema.json` | 摄取 skill 文档与 schema |
| Create | `skills/study-topic/SKILL.md` | 主题研读 skill 文档 |
| Rename+Modify | `skills/read-paper/` → `skills/read-source/`（含 `SKILL.md`、`references/analysis.schema.json`） | 单源精读泛化 |
| Modify | `skills/deposit-paper-knowledge/SKILL.md`、`references/wiki-schema.md` | 新集合与 kind 分派说明 |
| Modify | `README.md`、`docs/WORKFLOW.md` | 管线图、intent 表、组合规则 |

---

### Task 1: URL 身份助手（norm_url / url_source_id / classify_source）

**Files:**
- Modify: `paperwiki.py`（在 `paper_id` 定义之后、`arxiv_search` 之前插入）
- Create: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

创建 `tests/test_ingest.py`：

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_ingest -v`
Expected: FAIL / ERROR，报 `AttributeError: module 'paperwiki' has no attribute 'norm_url'`。

- [ ] **Step 3: Write the implementation**

在 `paperwiki.py` 的 `paper_id` 函数之后插入（保持文件的紧凑风格）：

```python
DOCS_HOST_PREFIXES=("docs.","platform.","developers.")
DOCS_HOSTS=("modelcontextprotocol.io",)

def norm_url(url):
    """Canonical URL for identity: https, lowercase host, no trailing slash, no tracking params, no fragment."""
    s=urllib.parse.urlsplit(url.strip())
    pairs=[(k,v) for k,v in urllib.parse.parse_qsl(s.query,keep_blank_values=True) if not k.lower().startswith(("utm_","ref"))]
    return urllib.parse.urlunsplit(("https",s.netloc.lower(),s.path.rstrip("/"),urllib.parse.urlencode(pairs),""))

def url_source_id(url):
    """Stable source identity: arXiv > DOI > hash of the normalized URL (spec §4.1)."""
    host=urllib.parse.urlsplit(url).netloc.lower()
    if host.endswith("arxiv.org"):
        aid=norm_arxiv(url)
        if aid: return "arxiv:"+aid
    m=re.search(r"doi\.org/(10\.\d{4,9}/[^\s?#]+)",url,re.I)
    if m: return "doi:"+m.group(1).rstrip("/").lower()
    return "url:"+hashlib.sha256(norm_url(url).encode()).hexdigest()[:12]

def classify_source(url):
    """Host heuristic: paper | github | docs | blog | other (spec §4.1)."""
    host=urllib.parse.urlsplit(url).netloc.lower()
    if not host: return "other"
    if host.endswith("arxiv.org") or host.endswith("doi.org"): return "paper"
    if host=="github.com" or host.endswith(".github.com"): return "github"
    if host.startswith(DOCS_HOST_PREFIXES) or host in DOCS_HOSTS: return "docs"
    if url.startswith(("http://","https://")): return "blog"
    return "other"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ingest -v`
Expected: 4 tests PASS（OK）。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_ingest.py
git commit -m "feat: url identity and source-type helpers for curated lists"
```

---

### Task 2: awesome README 解析器（parse_awesome_readme）

**Files:**
- Modify: `paperwiki.py`（紧接 Task 1 的函数之后）
- Modify: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

在 `tests/test_ingest.py` 顶部（`import paperwiki` 之后）加入共享 fixture 常量，并新增测试类：

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_ingest -v`
Expected: 新增 3 个测试 ERROR（`no attribute 'parse_awesome_readme'`），Task 1 的 4 个仍 PASS。

- [ ] **Step 3: Write the implementation**

在 `classify_source` 之后插入：

```python
ENTRY_RE=re.compile(r"^\s*-\s+\[([^\]]+)\]\((https?://[^)\s]+)\)(.*)$")

def parse_awesome_readme(text):
    """Parse an awesome-list README into normalized entries. Returns (entries, unparsed_lines)."""
    entries=[]; by_id={}; unparsed=[]; section=[]
    for line in text.splitlines():
        h=re.match(r"^(#{2,3})\s+(.*?)\s*$",line)
        if h:
            title=re.sub(r"^[^\w&]+","",h.group(2)).strip()
            section=[title] if len(h.group(1))==2 else (section[:1] or [""])+[title]
            continue
        if section and section[0].lower()=="contents": continue
        if not line.lstrip().startswith("- ["): continue
        m=ENTRY_RE.match(line)
        if not m: unparsed.append(line.strip()); continue
        title,url,rest=m.group(1).strip(),m.group(2),m.group(3)
        desc=" ".join(re.sub(r"^\s*[—–-]\s*","",re.sub(r"!\[[^\]]*\]\([^)]*\)","",rest).strip()).split())
        sid=url_source_id(url)
        if sid in by_id: by_id[sid].setdefault("also_in",[]).append(list(section)); continue
        entry={"source_id":sid,"title":title,"url":url,"source_type":classify_source(url),"section_path":list(section),"description":desc}
        by_id[sid]=entry; entries.append(entry)
    return entries,unparsed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ingest -v`
Expected: 7 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_ingest.py
git commit -m "feat: parse awesome-list README into normalized entries"
```

---

### Task 3: 清单 merge/diff（merge_reading_list）

**Files:**
- Modify: `paperwiki.py`
- Modify: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

追加到 `tests/test_ingest.py`：

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_ingest -v`
Expected: 新增 4 个 ERROR（`no attribute 'merge_reading_list'`）。

- [ ] **Step 3: Write the implementation**

在 `parse_awesome_readme` 之后插入：

```python
LIST_STATUSES=("unread","queued","skimmed","studied","deposited","blocked")
LIST_SYNC_KEYS=("title","url","source_type","section_path","description")

def merge_reading_list(existing,parsed,now):
    """Re-runnable sync: upstream metadata refreshes, local study state never overwritten (spec §4.1)."""
    old={e["source_id"]:e for e in existing}; merged=[]; added=[]; changed=[]
    for e in parsed:
        prev=old.pop(e["source_id"],None)
        if prev is None:
            entry=dict(e); entry.update({"status":"unread","added_at":now,"status_updated_at":now}); added.append(e["source_id"])
        else:
            entry=dict(prev)
            if any(prev.get(k)!=e.get(k) for k in LIST_SYNC_KEYS+("also_in",)): changed.append(e["source_id"])
            for k in LIST_SYNC_KEYS: entry[k]=e[k]
            if "also_in" in e: entry["also_in"]=e["also_in"]
            else: entry.pop("also_in",None)
            entry.pop("removed_upstream",None)
        merged.append(entry)
    removed=[]
    for prev in old.values():
        entry=dict(prev)
        if not prev.get("removed_upstream"): removed.append(prev["source_id"])
        entry["removed_upstream"]=True; merged.append(entry)
    return merged,{"added":added,"removed":removed,"changed":changed}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ingest -v`
Expected: 11 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_ingest.py
git commit -m "feat: re-runnable reading-list merge preserving study state"
```

---

### Task 4: `cmd_ingest` 与 CLI 接线

**Files:**
- Modify: `paperwiki.py`（`cmd_discover` 之后新增函数；`main()` 接线）
- Modify: `.gitignore`（curated 清单可版本化）
- Modify: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

追加到 `tests/test_ingest.py`：

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_ingest -v`
Expected: 前 3 个 ERROR（`no attribute 'cmd_ingest'`），CLI 测试 FAIL（argparse 报 invalid choice），gitignore 测试 FAIL（清单文件被忽略）。

- [ ] **Step 3: Write the implementation**

先改 `.gitignore`——`reading-lists/` 段由：

```gitignore
reading-lists/*
!reading-lists/.gitkeep
```

改为（curated 清单携带学习状态、需要版本化；discover/recommend 的临时输出保持忽略）：

```gitignore
reading-lists/*
!reading-lists/.gitkeep
!reading-lists/*.json
reading-lists/latest.json
reading-lists/recommended-next.json
```

然后在 `cmd_discover` 之后插入：

```python
def readme_source(value):
    """Resolve a local path / GitHub repo URL / raw URL to README text."""
    p=Path(value)
    if p.is_file(): return p.read_text(encoding="utf-8")
    m=re.match(r"https?://github\.com/([^/]+)/([^/#?]+)",value)
    if m: return fetch(f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2).removesuffix('.git')}/HEAD/README.md")
    if value.startswith(("http://","https://")): return fetch(value)
    raise ValueError("Provide a GitHub repo URL, a raw README URL, or a local README path")

def cmd_ingest(a):
    text=readme_source(a.source)
    list_slug=a.list_slug or slug(Path(urllib.parse.urlsplit(a.source).path or a.source).name.removesuffix(".git").removesuffix(".md"))
    out=Path(a.root)/"reading-lists"/f"{list_slug}.json"
    existing=json.loads(out.read_text(encoding="utf-8")).get("entries",[]) if out.exists() else []
    parsed,unparsed=parse_awesome_readme(text); now=dt.datetime.now(dt.timezone.utc).isoformat()
    entries,diff=merge_reading_list(existing,parsed,now)
    payload={"list_slug":list_slug,"source_repo":a.source,"retrieved_at":now,"entries":entries}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    status_counts={}; section_counts={}
    for e in entries:
        status_counts[e["status"]]=status_counts.get(e["status"],0)+1
        top=(e.get("section_path") or ["(none)"])[0]; section_counts[top]=section_counts.get(top,0)+1
    print(json.dumps({"list":str(out),"total":len(entries),"status_counts":status_counts,"section_counts":section_counts,"diff":diff,"unparsed_lines":unparsed},ensure_ascii=False,indent=2))
```

`main()` 中，在 `recommend` 的 add_parser 行之后加：

```python
    i=sub.add_parser("ingest"); i.add_argument("source",help="Awesome-list GitHub URL, raw README URL, or local README path"); i.add_argument("--list-slug",default=None); i.add_argument("--root",default="."); i.set_defaults(func=cmd_ingest)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ingest -v`
Expected: 16 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py .gitignore tests/test_ingest.py
git commit -m "feat: ingest command syncs awesome lists into reading-lists/"
```

---

### Task 5: `cmd_mark` 与状态机（mark_list_entries）

**Files:**
- Modify: `paperwiki.py`
- Modify: `tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

追加到 `tests/test_ingest.py`：

```python
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

    def test_cmd_mark_resolves_slug_via_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._seed_list(root)
            paperwiki.cmd_mark(type("A", (), {"list": "hx", "source_ids": ["url:aaa"],
                                              "status": "queued", "reason": None, "root": str(root)}))
            entry = json.loads((root / "reading-lists/hx.json").read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "queued")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_ingest -v`
Expected: 新增 4 个 ERROR（`no attribute 'mark_list_entries'`）。

- [ ] **Step 3: Write the implementation**

在 `cmd_ingest` 之后插入：

```python
def mark_list_entries(list_path,source_ids,status,reason=None):
    """Move reading-list entries through the study state machine (spec §4.1)."""
    if status not in LIST_STATUSES: raise ValueError(f"status must be one of {LIST_STATUSES}")
    if status=="blocked" and not reason: raise ValueError("blocked requires a --reason")
    path=Path(list_path); data=json.loads(path.read_text(encoding="utf-8")); now=dt.datetime.now(dt.timezone.utc).isoformat(); hit=0
    for e in data.get("entries",[]):
        if e.get("source_id") in source_ids:
            e["status"]=status; e["status_updated_at"]=now
            if reason: e["blocked_reason"]=reason
            elif status!="blocked": e.pop("blocked_reason",None)
            hit+=1
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8"); return hit

def cmd_mark(a):
    path=Path(a.list) if Path(a.list).is_file() else Path(a.root)/"reading-lists"/f"{a.list}.json"
    if not path.exists(): raise FileNotFoundError(f"Reading list not found: {path}")
    hit=mark_list_entries(path,set(a.source_ids),a.status,getattr(a,"reason",None))
    print(f"{hit}/{len(set(a.source_ids))} entries -> {a.status} in {path}")
```

`main()` 中，在 `ingest` 接线行之后加：

```python
    mk=sub.add_parser("mark"); mk.add_argument("list",help="Reading-list slug or path"); mk.add_argument("source_ids",nargs="+"); mk.add_argument("--status",required=True,choices=LIST_STATUSES); mk.add_argument("--reason"); mk.add_argument("--root",default="."); mk.set_defaults(func=cmd_mark)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ingest -v`
Expected: 20 tests PASS。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_ingest.py
git commit -m "feat: mark command drives reading-list study states"
```

---

### Task 6: `cmd_read` 泛化（github / web 分支 + arXiv 误判防护）

**Files:**
- Modify: `paperwiki.py:171-192`（`cmd_read`）
- Create: `tests/test_read_source.py`

- [ ] **Step 1: Write the failing tests**

创建 `tests/test_read_source.py`：

```python
"""L1 verification of `read` for non-paper sources: github/web branches, identity, skeleton."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paperwiki


class ReadSourceTests(unittest.TestCase):
    def _args(self, root, target, slug=None):
        return type("A", (), {"paper": target, "root": str(root), "report_slug": slug})

    def test_read_github_repo_creates_source_record(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                self.assertEqual(url, "https://raw.githubusercontent.com/microsoft/TaskWeaver/HEAD/README.md")
                return "# TaskWeaver\n\nA code-first agent framework."

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(root, "https://github.com/microsoft/TaskWeaver", "taskweaver"))

            record = json.loads((root / "reports/taskweaver/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "source")
            self.assertEqual(record["source_type"], "github")
            self.assertEqual(record["title"], "microsoft/TaskWeaver")
            self.assertTrue(record["paper_id"].startswith("url:"))
            report = (root / "reports/taskweaver/report.md").read_text(encoding="utf-8")
            self.assertIn("read-source", report)
            self.assertNotIn("paper-analyzer", report)

    def test_read_blog_url_creates_source_record_with_page_title(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                return "<html><head><title>Effective Context  Engineering</title></head><body>x</body></html>"

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(
                    root, "https://www.anthropic.com/engineering/effective-context-engineering", "ece"))

            record = json.loads((root / "reports/ece/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["source_type"], "blog")
            self.assertEqual(record["title"], "Effective Context Engineering")
            self.assertEqual(record["paper_id"],
                             paperwiki.url_source_id("https://www.anthropic.com/engineering/effective-context-engineering"))

    def test_non_arxiv_url_with_digit_pattern_is_not_misread_as_arxiv(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_fetch(url, binary=False):
                self.assertNotIn("export.arxiv.org", url)
                return "<html><head><title>Post 2024.12345</title></head><body>x</body></html>"

            with patch.object(paperwiki, "fetch", fake_fetch):
                paperwiki.cmd_read(self._args(root, "https://blog.example.com/2024.12345-post", "post"))

            record = json.loads((root / "reports/post/record.json").read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "source")

    def test_paper_record_has_no_source_kind(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdf = root / "Local Paper.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            paperwiki.cmd_read(self._args(root, str(pdf)))
            record = json.loads((root / "reports/local-paper/record.json").read_text(encoding="utf-8"))
            self.assertNotIn("kind", record)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_read_source -v`
Expected: 前 3 个 FAIL/ERROR（github URL 落进 `ValueError: Provide an arXiv URL/ID...`；digit-pattern URL 被误判走 arXiv 分支）。第 4 个 PASS（现状即无 kind）。

- [ ] **Step 3: Write the implementation**

修改 `cmd_read`。函数开头两行由：

```python
    aid=norm_arxiv(a.paper); local=Path(a.paper); doi=None; pdf_bytes=None
    doi_match=re.search(r"(?:doi\.org/)?(10\.\d{4,9}/\S+)",a.paper,re.I)
```

改为（先算 doi_match，再用 URL 语境约束 arXiv 匹配，修复 `\d{4}\.\d{4,5}` 对普通 URL/DOI 的误判）：

```python
    local=Path(a.paper); doi=None; pdf_bytes=None
    doi_match=re.search(r"(?:doi\.org/)?\b(10\.\d{4,9}/\S+)",a.paper,re.I)
    is_url=a.paper.startswith(("http://","https://"))
    aid=norm_arxiv(a.paper) if not doi_match and (not is_url or "arxiv.org" in a.paper.lower()) else None
```

在 `elif a.paper.startswith(("http://","https://")) and ".pdf" in a.paper.lower():` 分支之后、`else: raise ValueError(...)` 之前，插入两个新分支：

```python
    elif re.match(r"https?://github\.com/[^/]+/[^/#?]+",a.paper):
        m=re.match(r"https?://github\.com/([^/]+)/([^/#?]+)",a.paper); owner,repo=m.group(1),m.group(2).removesuffix(".git")
        try: readme=fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md")
        except Exception: readme=""
        p={"title":f"{owner}/{repo}","authors":[],"abstract":" ".join(readme.split())[:600] or None,"source_url":a.paper,"kind":"source","source_type":"github","provenance":[{"provider":"github-readme","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}
    elif is_url:
        page=fetch(a.paper); tm=re.search(r"<title[^>]*>(.*?)</title>",page,re.S|re.I)
        p={"title":html.unescape(" ".join(tm.group(1).split())) if tm else norm_url(a.paper),"authors":[],"source_url":a.paper,"kind":"source","source_type":classify_source(a.paper),"provenance":[{"provider":"web-page","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}
```

身份行由 `p["paper_id"]=paper_id(p); p["status"]="reading"` 改为：

```python
    p["paper_id"]=url_source_id(p["source_url"]) if p.get("kind")=="source" else paper_id(p); p["status"]="reading"
```

报告骨架 `report.write_text(...)` 一行改为按 kind 切换分析引导块（保持一行式风格，先在其前面提两个变量）：

```python
    if p.get("kind")=="source": section,guidance="## Deep-read analysis",f"> Deep-read {p.get('source_url')} following `skills/read-source/SKILL.md`; cite section/heading (blog, docs) or file-path (repo) locators, write `analysis.json` beside this report, then run finalize."
    else: section,guidance="## Paper Craft analysis",f"> Run `$paper-analyzer` from `vendor/paper-craft-skills` against `{p.get('pdf_path') or p.get('source_url')}` and replace this block with the reviewed analysis."
    report.write_text(f"---\npaper_id: {p['paper_id']}\nstatus: reading\nsource: {p.get('source_url') or str(local)}\n---\n\n# {p['title']}\n\n## Abstract\n\n{p.get('abstract') or 'Metadata source did not provide an abstract.'}\n\n{section}\n\n{guidance}\n\n## User notes\n\n",encoding="utf-8"); p["reading"]={"report_path":str(report),"paper_craft_skill":"paper-analyzer" if p.get("kind")!="source" else None,"analysis_status":"pending-agent-review","full_text_available":bool(pdf_bytes)}; paths["record"].write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding="utf-8"); print(report)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_read_source tests.test_paperwiki -v`
Expected: 全部 PASS（含既有 `test_paperwiki` 回归：本地 PDF、slug 碰撞等行为不变）。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_read_source.py
git commit -m "feat: read command accepts github repos and web articles as sources"
```

---

### Task 7: `cmd_finalize` 条件校验 + analysis schema

**Files:**
- Modify: `paperwiki.py:196-206`（`cmd_finalize`）
- Modify: `tests/test_finalize.py`
- Modify: `skills/read-paper/references/analysis.schema.json`

- [ ] **Step 1: Write the failing tests**

在 `tests/test_finalize.py` 中 `FULL_ANALYSIS` 之后加入 source 用 fixture 与 seeding 函数，并新增测试类：

```python
SOURCE_ANALYSIS = {
    "tldr": "one line", "research_question": "Q", "contributions": ["C"], "method": "M",
    "findings": ["F"], "limitations": ["L"], "concepts": ["Context Rot"],
    "methods": ["Compaction"], "topics": ["Context Engineering"], "open_questions": ["Q?"],
}


def _seed_source(root, analysis):
    folder = root / "reports/ece"
    folder.mkdir(parents=True, exist_ok=True)
    report = folder / "report.md"
    report.write_text("# draft", encoding="utf-8")
    record = {"paper_id": "url:abcdef123456", "title": "Effective Context Engineering",
              "kind": "source", "source_type": "blog",
              "source_url": "https://www.anthropic.com/engineering/x",
              "reading": {"report_path": str(report)}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    ap = folder / "analysis.json"
    ap.write_text(json.dumps(analysis), encoding="utf-8")
    return report, ap


class FinalizeSourceTests(unittest.TestCase):
    def test_source_analysis_passes_without_paper_only_fields(self):
        with tempfile.TemporaryDirectory() as td:
            report, ap = _seed_source(Path(td), dict(SOURCE_ANALYSIS))
            paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            text = report.read_text(encoding="utf-8")
            self.assertIn("status: reviewed", text)

    def test_source_analysis_still_requires_core_fields(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(SOURCE_ANALYSIS)
            del incomplete["findings"]
            report, ap = _seed_source(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("findings", str(cm.exception))

    def test_paper_analysis_gate_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            incomplete = dict(FULL_ANALYSIS)
            del incomplete["experiments"]
            report, ap = _seed(Path(td), incomplete)
            with self.assertRaises(ValueError) as cm:
                paperwiki.cmd_finalize(type("A", (), {"report": str(report), "analysis": str(ap)}))
            self.assertIn("experiments", str(cm.exception))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_finalize -v`
Expected: `test_source_analysis_passes_without_paper_only_fields` FAIL（缺 experiments 等字段被拒）；其余两个 PASS。

- [ ] **Step 3: Write the implementation**

模块级（`WEIGHTS` 附近）加常量：

```python
REQUIRED_PAPER_ANALYSIS=["research_question","contributions","method","experiments","findings","limitations","reproducibility","concepts","methods","datasets","topics","open_questions"]
REQUIRED_SOURCE_ANALYSIS=["research_question","contributions","method","findings","limitations","concepts","methods","topics","open_questions"]
```

`cmd_finalize` 中：

```python
    required=["research_question","contributions","method","experiments","findings","limitations","reproducibility","concepts","methods","datasets","topics","open_questions"]
```

改为：

```python
    required=REQUIRED_SOURCE_ANALYSIS if p.get("kind")=="source" else REQUIRED_PAPER_ANALYSIS
```

报告模板 f-string 中两处改为容忍缺失（论文仍必填，行为不变）：

- `{bullets(analysis['experiments'])}` → `{bullets(analysis.get('experiments',[]))}`
- `{bullets(analysis['reproducibility'])}` → `{bullets(analysis.get('reproducibility',[]))}`

`skills/read-paper/references/analysis.schema.json` 的 `properties` 中追加一行（`"mermaid"` 之后，注意补逗号）：

```json
    "source_type": {"enum": ["paper", "blog", "docs", "github", "other"], "description": "Non-paper sources (record kind: source) may omit experiments, reproducibility, and datasets; evidence locators are section/heading for blog+docs and file paths for github. The CLI enforces the relaxed gate."}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_finalize -v`
Expected: 10 tests PASS（7 个既有 + 3 个新增）。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_finalize.py skills/read-paper/references/analysis.schema.json
git commit -m "feat: finalize validates source analyses with a relaxed gate"
```

---

### Task 8: `cmd_deposit` 支持 `kind: source`（wiki/sources 页）

**Files:**
- Modify: `paperwiki.py:313-336`（`link_entity`、`cmd_deposit`）
- Create: `tests/test_deposit_kinds.py`

- [ ] **Step 1: Write the failing tests**

创建 `tests/test_deposit_kinds.py`：

```python
"""L1 verification of deposit for kind: source and kind: topic records."""
import json
import tempfile
import unittest
from pathlib import Path

import paperwiki


def _seed_source_report(root):
    folder = root / "reports/ece"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text("---\npaper_id: url:abcdef123456\n---\n\n# Effective Context Engineering\n\nBody\n",
                      encoding="utf-8")
    record = {"paper_id": "url:abcdef123456", "title": "Effective Context Engineering",
              "kind": "source", "source_type": "blog",
              "source_url": "https://www.anthropic.com/engineering/x",
              "reading": {"concepts": ["Context Rot"], "methods": ["Compaction"],
                          "datasets": [], "topics": ["Context Engineering"], "tools": ["LLMLingua"]}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    return report


class DepositSourceTests(unittest.TestCase):
    def test_source_record_lands_in_wiki_sources_with_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            self.assertEqual(list((root / "wiki").glob("papers/*.md")), [])
            page = next((root / "wiki/sources").glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("source_type: blog", page)
            self.assertIn("url: https://www.anthropic.com/engineering/x", page)
            self.assertIn("[[reports/ece/report|Effective Context Engineering report]]", page)

    def test_source_deposit_links_tools_collection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            tool = (root / "wiki/tools/llmlingua.md").read_text(encoding="utf-8")
            self.assertIn("type: tool", tool)
            self.assertIn("Effective Context Engineering", tool)

    def test_source_deposit_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_source_report(root)
            args = type("A", (), {"input": str(report), "root": str(root)})
            paperwiki.cmd_deposit(args)
            paperwiki.cmd_deposit(args)
            self.assertEqual(len(list((root / "wiki/sources").glob("*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_deposit_kinds -v`
Expected: 3 个 FAIL（页面落在 `wiki/papers/`，无 source frontmatter，无 tools 页）。

- [ ] **Step 3: Write the implementation**

`link_entity` 签名加 heading 参数（默认值保持既有行为，现有调用与既有 wiki 页零变化）：

```python
def link_entity(root, collection, name, page_title, page_target, heading="Related papers"):
    folder=root/"wiki"/collection; folder.mkdir(parents=True,exist_ok=True); target=folder/(slug(name)+".md")
    link=f"- [[{page_target}|{page_title}]]\n"; old=target.read_text(encoding="utf-8") if target.exists() else f"---\ntitle: \"{name.replace(chr(34),chr(39))}\"\ntype: {collection.rstrip('s')}\n---\n\n# {name}\n\n## {heading}\n\n"
    target.write_text(old if link in old else old+link,encoding="utf-8"); return f"[[{target.stem}|{name}]]"
```

`cmd_deposit` 改造（完整替换函数；paper 行为与现文逐语句一致，仅抽出 kind/collection 变量）：

```python
def cmd_deposit(a):
    src=Path(a.input); text=src.read_text(encoding="utf-8"); side=resolve_record_path(src,diagnose=True); p=json.loads(side.read_text(encoding="utf-8")) if side.exists() else {"title":re.search(r"^#\s+(.+)$",text,re.M).group(1),"provenance":[{"provider":"user-notes","path":str(src)}]}
    kind=p.get("kind") or "paper"; root=Path(a.root)
    if kind=="topic": return deposit_topic(a,src,p)
    p["paper_id"]=p.get("paper_id") or paper_id(p)
    collection="sources" if kind=="source" else "papers"; heading="Related pages" if kind=="source" else "Related papers"
    pages=root/"wiki"/collection; pages.mkdir(parents=True,exist_ok=True)
    target=pages/(slug(p["paper_id"])+".md"); existing=target.read_text(encoding="utf-8") if target.exists() else ""; human=""
    m=re.search(r"## User notes\s*(.*?)(?=\n## |\Z)",existing,re.S)
    if m: human=m.group(1).strip()
    reading=p.get("reading") or {}; entities=[]
    for key,coll in [("concepts","concepts"),("methods","methods"),("datasets","datasets"),("topics","topics"),("tools","tools")]:
        for name in reading.get(key,[]) or []: entities.append(link_entity(root,coll,str(name),p["title"],target.stem,heading=heading))
    source_target=report_wikilink_target(src,root)
    source_reference=f"[[{source_target}|{p['title']} report]]" if source_target else f"`{src.resolve()}`"
    synthesis_text=strip_leading_frontmatter(text)
    extra=f"\nsource_type: {p.get('source_type','other')}\nurl: {p.get('source_url','')}" if kind=="source" else ""
    body=f"---\npaper_id: {p['paper_id']}\ntitle: \"{p['title'].replace(chr(34),chr(39))}\"\nstatus: deposited{extra}\n---\n\n# {p['title']}\n\n## Source report\n\n{source_reference}\n\n## Related knowledge\n\n"+("\n".join(f"- {x}" for x in entities) if entities else "- No structured entities confirmed yet.")+f"\n\n## Generated synthesis (draft)\n\n{synthesis_text}\n\n## User notes\n\n{human}\n"
    target.write_text(body,encoding="utf-8"); (root/"index.md").parent.mkdir(parents=True,exist_ok=True); idx=root/"index.md"; line=f"- [[{target.stem}|{p['title']}]]\n"; old=idx.read_text(encoding="utf-8") if idx.exists() else "# PaperWiki Index\n\n"; idx.write_text(old if line in old else old+line,encoding="utf-8")
    log=root/"log.md"; old=log.read_text(encoding="utf-8") if log.exists() else "# Operation Log\n\n"; log.write_text(old+f"- {dt.datetime.now(dt.timezone.utc).isoformat()} deposit {p['paper_id']}\n",encoding="utf-8"); print(target)
```

同时加一个占位的 `deposit_topic`（Task 9 实现；先抛错以保证本任务独立可测）：

```python
def deposit_topic(a,src,p):
    raise NotImplementedError("kind: topic deposits arrive in the next commit")
```

注意：`("tools","tools")` 映射对论文记录无影响——论文 `reading` 里没有 `tools` 键，`reading.get(key,[]) or []` 得空列表。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_deposit_kinds tests.test_deposit tests.test_paperwiki -v`
Expected: 全部 PASS（既有 deposit 回归全绿）。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_deposit_kinds.py
git commit -m "feat: deposit source records into wiki/sources with tools links"
```

---

### Task 9: `cmd_deposit` 支持 `kind: topic`（主题图谱页 + 清单状态回写）

**Files:**
- Modify: `paperwiki.py`（实现 `deposit_topic`、新增 `link_source_page`）
- Modify: `tests/test_deposit_kinds.py`

- [ ] **Step 1: Write the failing tests**

追加到 `tests/test_deposit_kinds.py`：

```python
def _seed_topic_report(root, with_list=False):
    folder = root / "reports/topic-context-compaction"
    folder.mkdir(parents=True)
    report = folder / "report.md"
    report.write_text("---\ntopic_id: context-compaction\nkind: topic\n---\n\n# 上下文压缩综述\n\n正文\n",
                      encoding="utf-8")
    record = {"kind": "topic", "topic_slug": "context-compaction", "title": "Context Compaction",
              "list_slug": "hx" if with_list else None,
              "sources": [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                           "url": "https://platform.claude.com/docs/compaction",
                           "source_type": "docs", "role": "core", "status": "studied"}],
              "entities": {"concepts": ["Context Rot"], "methods": ["Progressive Compaction"],
                           "tools": ["LLMLingua"]},
              "created": "T0", "updated": "T0"}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    if with_list:
        lp = root / "reading-lists/hx.json"
        lp.parent.mkdir(parents=True)
        lp.write_text(json.dumps({"list_slug": "hx", "source_repo": "r", "retrieved_at": "T0",
                                  "entries": [{"source_id": "url:aaa111222333", "title": "Compaction Docs",
                                               "url": "https://platform.claude.com/docs/compaction",
                                               "source_type": "docs", "section_path": ["S"],
                                               "description": "", "status": "studied",
                                               "added_at": "T0", "status_updated_at": "T0"}]}),
                      encoding="utf-8")
    return report


class DepositTopicTests(unittest.TestCase):
    def test_topic_record_builds_english_graph_page(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            page = (root / "wiki/topics/context-compaction.md").read_text(encoding="utf-8")
            self.assertIn("type: topic", page)
            self.assertIn("[[reports/topic-context-compaction/report|Context Compaction 综述]]", page)
            self.assertIn("[[progressive-compaction|Progressive Compaction]]", page)
            self.assertIn("[[llmlingua|LLMLingua]]", page)
            self.assertIn("[[compaction-docs|Compaction Docs]]", page)
            source_page = (root / "wiki/sources/compaction-docs.md").read_text(encoding="utf-8")
            self.assertIn("url: https://platform.claude.com/docs/compaction", source_page)
            self.assertIn("source_id: url:aaa111222333", source_page)
            self.assertIn("Context Compaction", source_page)
            self.assertIn("Context Compaction", (root / "index.md").read_text(encoding="utf-8"))
            self.assertIn("deposit topic:context-compaction", (root / "log.md").read_text(encoding="utf-8"))

    def test_topic_deposit_preserves_existing_related_papers_and_notes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)
            topics = root / "wiki/topics"
            topics.mkdir(parents=True)
            (topics / "context-compaction.md").write_text(
                "---\ntitle: \"Context Compaction\"\ntype: topic\n---\n\n# Context Compaction\n\n"
                "## Related papers\n\n- [[arxiv-1234-5678|Old Paper]]\n\n## User notes\n\nkeep me\n",
                encoding="utf-8")

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            page = (topics / "context-compaction.md").read_text(encoding="utf-8")
            self.assertIn("[[arxiv-1234-5678|Old Paper]]", page)
            self.assertIn("keep me", page)

    def test_topic_deposit_marks_list_entries_deposited(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root, with_list=True)

            paperwiki.cmd_deposit(type("A", (), {"input": str(report), "root": str(root)}))

            entry = json.loads((root / "reading-lists/hx.json").read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(entry["status"], "deposited")

    def test_topic_deposit_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = _seed_topic_report(root)
            args = type("A", (), {"input": str(report), "root": str(root)})
            paperwiki.cmd_deposit(args)
            paperwiki.cmd_deposit(args)
            page = (root / "wiki/topics/context-compaction.md").read_text(encoding="utf-8")
            self.assertEqual(page.count("[[llmlingua|LLMLingua]]"), 1)
            self.assertEqual(len(list((root / "wiki/sources").glob("*.md"))), 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_deposit_kinds -v`
Expected: 4 个新测试 ERROR（`NotImplementedError`）。

- [ ] **Step 3: Write the implementation**

用以下实现替换占位 `deposit_topic`，并在其前面加 `link_source_page`：

```python
def link_source_page(root,source,page_title,page_target):
    """Create or update a wiki/sources stub for a studied source; append the backlink idempotently."""
    folder=root/"wiki/sources"; folder.mkdir(parents=True,exist_ok=True)
    name=str(source.get("title") or source.get("url") or source.get("source_id") or "source")
    target=folder/(slug(name)+".md"); link=f"- [[{page_target}|{page_title}]]\n"
    old=target.read_text(encoding="utf-8") if target.exists() else f"---\ntitle: \"{name.replace(chr(34),chr(39))}\"\ntype: source\nsource_type: {source.get('source_type','other')}\nurl: {source.get('url','')}\nsource_id: {source.get('source_id','')}\n---\n\n# {name}\n\n## Related pages\n\n"
    target.write_text(old if link in old else old+link,encoding="utf-8"); return f"[[{target.stem}|{name}]]"

def deposit_topic(a,src,p):
    """Deposit a topic synthesis record: short English graph page linking the Chinese report (spec §4.4)."""
    root=Path(a.root); tslug=slug(p.get("topic_slug") or p["title"]); folder=root/"wiki/topics"; folder.mkdir(parents=True,exist_ok=True)
    target=folder/(tslug+".md"); existing=target.read_text(encoding="utf-8") if target.exists() else ""; human=""
    m=re.search(r"## User notes\s*(.*?)(?=\n## |\Z)",existing,re.S)
    if m: human=m.group(1).strip()
    rp=re.search(r"## Related papers\s*(.*?)(?=\n## |\Z)",existing,re.S); related_papers=rp.group(1).strip() if rp else ""
    ent=p.get("entities") or {}; entities=[]
    for key,coll in [("concepts","concepts"),("methods","methods"),("tools","tools")]:
        for name in ent.get(key,[]) or []: entities.append(link_entity(root,coll,str(name),p["title"],target.stem,heading="Related pages"))
    sources=[link_source_page(root,s_,p["title"],target.stem) for s_ in p.get("sources") or []]
    report_target=report_wikilink_target(src,root)
    ref=f"[[{report_target}|{p['title']} 综述]]" if report_target else f"`{src.resolve()}`"
    papers_block=f"\n\n## Related papers\n\n{related_papers}" if related_papers else ""
    body=f"---\ntitle: \"{p['title'].replace(chr(34),chr(39))}\"\ntype: topic\nstatus: deposited\n---\n\n# {p['title']}\n\n## Synthesis report\n\n{ref}\n\n## Sources\n\n"+("\n".join(f"- {x}" for x in sources) if sources else "- None recorded.")+"\n\n## Related knowledge\n\n"+("\n".join(f"- {x}" for x in entities) if entities else "- No structured entities confirmed yet.")+papers_block+f"\n\n## User notes\n\n{human}\n"
    target.write_text(body,encoding="utf-8")
    idx=root/"index.md"; line=f"- [[{target.stem}|{p['title']}]]\n"; old=idx.read_text(encoding="utf-8") if idx.exists() else "# PaperWiki Index\n\n"; idx.write_text(old if line in old else old+line,encoding="utf-8")
    log=root/"log.md"; old=log.read_text(encoding="utf-8") if log.exists() else "# Operation Log\n\n"; log.write_text(old+f"- {dt.datetime.now(dt.timezone.utc).isoformat()} deposit topic:{tslug}\n",encoding="utf-8")
    lp=root/"reading-lists"/f"{p.get('list_slug') or ''}.json"
    if p.get("list_slug") and lp.exists(): mark_list_entries(lp,{s_.get("source_id") for s_ in p.get("sources") or [] if s_.get("source_id")},"deposited")
    print(target)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_deposit_kinds tests.test_deposit tests.test_paperwiki tests.test_ingest -v`
Expected: 全部 PASS。

- [ ] **Step 5: Commit**

```bash
git add paperwiki.py tests/test_deposit_kinds.py
git commit -m "feat: deposit topic syntheses into wiki/topics with list writeback"
```

---

### Task 10: `ingest-reading-list` skill 文档 + schema

**Files:**
- Create: `skills/ingest-reading-list/SKILL.md`
- Create: `skills/ingest-reading-list/references/reading-list.schema.json`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: ingest-reading-list
description: Use when the user asks to import, sync, refresh, or track a curated reading list (an awesome list or similar link collection) into PaperWiki, or asks what is new upstream or how far their study of a list has progressed.
---

# Ingest Reading List

## Workflow

1. Accept a GitHub repo URL, raw README URL, or local README path. Run `python paperwiki.py ingest <source> --list-slug <slug>`; the slug defaults to the repo name.
2. The parser maps `##`/`###` headings to `section_path` and `- [Title](url) — description` lines to entries; the `Contents` section is skipped and badges are stripped from descriptions. Entries conform to `references/reading-list.schema.json`.
3. Identity is `arxiv:<id>` > `doi:<doi>` > `url:<sha256-12>` of the normalized URL, matching the pipeline-wide rule; arXiv entries later merge with the paper pipeline automatically.
4. Source types come from host heuristics (`paper | github | blog | docs | other`); report obvious misclassifications instead of silently accepting them.
5. Re-running the same command is the update mechanism: report the printed diff (added / removed-upstream / changed) and unparsed lines to the user. Never edit `status` fields during ingest.
6. Use `python paperwiki.py mark <slug> <source_id ...> --status <status> [--reason <text>]` to move entries through `unread → queued → skimmed → studied → deposited`; `blocked` requires a reason.

## Guardrails

- Never delete entries that disappeared upstream; they stay flagged `removed_upstream`.
- Unparsed lines go to the diff summary, not to the void; surface them.
- Do not start reading or depositing content unless the user asks; ingestion is bookkeeping only.
```

- [ ] **Step 2: Write references/reading-list.schema.json**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["list_slug", "source_repo", "retrieved_at", "entries"],
  "properties": {
    "list_slug": {"type": "string"},
    "source_repo": {"type": "string"},
    "retrieved_at": {"type": "string"},
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["source_id", "title", "url", "source_type", "section_path", "description", "status", "added_at", "status_updated_at"],
        "properties": {
          "source_id": {"type": "string", "pattern": "^(arxiv:|doi:|url:)"},
          "title": {"type": "string"},
          "url": {"type": "string"},
          "source_type": {"enum": ["paper", "github", "blog", "docs", "other"]},
          "section_path": {"type": "array", "items": {"type": "string"}},
          "also_in": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
          "description": {"type": "string"},
          "status": {"enum": ["unread", "queued", "skimmed", "studied", "deposited", "blocked"]},
          "added_at": {"type": "string"},
          "status_updated_at": {"type": "string"},
          "notes": {"type": "string"},
          "blocked_reason": {"type": "string"},
          "removed_upstream": {"type": "boolean"}
        }
      }
    }
  }
}
```

- [ ] **Step 3: Verify and commit**

Run: `python - <<'EOF'
import json; json.load(open("skills/ingest-reading-list/references/reading-list.schema.json")); print("ok")
EOF`
Expected: `ok`

```bash
git add skills/ingest-reading-list
git commit -m "docs: ingest-reading-list skill and reading-list schema"
```

---

### Task 11: `study-topic` skill 文档

**Files:**
- Create: `skills/study-topic/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: study-topic
description: Use when the user asks to study, learn, survey, or synthesize a topic from a PaperWiki reading list (for example a section of an awesome list) or an ad-hoc set of sources, producing one Chinese synthesis report across several sources.
---

# Study Topic

## Workflow

1. Accept a reading-list section (e.g. "Context Delivery & Compaction" in `reading-lists/harness-engineering.json`) or a hand-picked set of entries. Confirm scope with the user when the section holds more than ~10 entries.
2. Select 5–8 core sources: foundational essays first, then one representative per `source_type`. Record the selection rationale in the report; list what was deliberately left out.
3. Fetch and read each source (GitHub repos to README + docs depth). Keep source claims and personal interpretation in separate sentences; never invent content. A source that cannot be fetched is marked `blocked` with a reason via `python paperwiki.py mark <list> <source_id> --status blocked --reason <why>`, and the synthesis states the evidence gap.
4. Write the Chinese synthesis to `reports/topic-<slug>/report.md` with sections: 主题界定 → 核心问题 → 模式对比 → 各来源观点与证据 → 工具盘点 → 开放问题与实践启发 → 来源清单. Follow Obsidian-safe conventions: no inline `$` math inside list items, no bare `*`, no 【】 source tags.
5. Report frontmatter: `topic_id`, `kind: topic`, `list_slug`, `sources` (source_id list), `status`, `generated: true`, `human_confirmed: false`.
6. Write `record.json` beside the report: `{kind: "topic", topic_slug, title, list_slug, sources: [{source_id, title, url, source_type, role: core|flagship|referenced, status}], entities: {concepts, methods, tools}, created, updated}`. Topic reports do NOT get an `analysis.json` and do NOT run `finalize`; render HTML with `python scripts/render_report.py reports/topic-<slug>/report.md reports/topic-<slug>/report.html` when asked.
7. Mark studied entries: `python paperwiki.py mark <list> <source_id ...> --status studied`.
8. When a flagship source deserves a standalone deep read, recommend `read-source` for it — do not run it automatically, and do not auto-deposit.

## Guardrails

- Separate 来源观点 from 我的解读 in every synthesis section.
- Cite locators: section/heading for blogs and docs, file paths for repos, page/figure for papers.
- Record failures as recoverable state; a blocked source never silently disappears from the 来源清单.
```

- [ ] **Step 2: Verify and commit**

Run: `head -5 skills/study-topic/SKILL.md`
Expected: frontmatter 以 `name: study-topic` 开头。

```bash
git add skills/study-topic
git commit -m "docs: study-topic skill for multi-source topic syntheses"
```

---

### Task 12: `read-paper` → `read-source` 改名与 SKILL.md 泛化

**Files:**
- Rename: `skills/read-paper/` → `skills/read-source/`
- Modify: `skills/read-source/SKILL.md`

- [ ] **Step 1: git mv**

```bash
git mv skills/read-paper skills/read-source
```

- [ ] **Step 2: Rewrite SKILL.md**

将 `skills/read-source/SKILL.md` 的 frontmatter 与正文更新为（保留原 workflow 步骤语义，新增 source 分派）：

```markdown
---
name: read-source
description: Use when the user supplies a paper URL, DOI, arXiv ID, local PDF, title, discovery record, engineering blog post, documentation page, or GitHub repository and asks to read, summarize, explain, review, or study that single source in depth.
---

# Read Source

## Workflow

1. Accept a URL, DOI, arXiv ID, local PDF, title, or PaperWiki record. Do not require discovery metadata. `python paperwiki.py read <input> --report-slug <slug>` detects the source type: arXiv/DOI/PDF → paper; github.com → github; other URLs → blog/docs.
2. Resolve metadata and accessible full text. Preserve original input, resolved URL, retrieval time, and source path.
3. **Papers** follow the unchanged deep-read path: invoke `vendor/paper-craft-skills/skills/paper-analyzer/SKILL.md`; evidence cites page/section/figure. **Blogs and docs**: read the full text; evidence cites section/heading. **Repos**: read README, docs, and key entry points; evidence cites file paths.
4. Choose the official abbreviation or repo name as the lowercase slug. Write `reports/<slug>/analysis.json`. Non-paper sources may omit `experiments`, `reproducibility`, and `datasets` (the relaxed gate is enforced by finalize; see `references/analysis.schema.json`). Include `source_type` in the analysis.
5. Run `python paperwiki.py finalize reports/<slug>/report.md reports/<slug>/analysis.json` to generate the readable report and update `record.json`.
6. Separate source claims, interpretation, and user notes. Keep the canonical artifact set `report.md`, `report.html`, `analysis.json`, `record.json`. Set `reviewed` only after user confirmation.

## Guardrails

- Flag inaccessible pages, paywalls, OCR uncertainty, and unsupported claims.
- Never invent venue, citation, experiment, benchmark, or code information.
- Do not automatically invoke `deposit-paper-knowledge`.
```

- [ ] **Step 3: Update repo references to the old name**

Run: `grep -rn "read-paper" README.md docs/ skills/ --include="*.md" | grep -v superpowers`
对每个命中处把 `read-paper` 改为 `read-source`（`docs/superpowers/` 下的 spec/plan 历史文档不改）。已知命中：`README.md`（管线图与 Skills 清单）、`docs/WORKFLOW.md`（intent 表）、`skills/deposit-paper-knowledge/SKILL.md`（description 里的 "reports not produced by read-paper"）。Task 14 会重写 README/WORKFLOW 相关段落，此处先做机械替换保证无悬空引用。

- [ ] **Step 4: Verify and commit**

Run: `grep -rn "read-paper" README.md docs/WORKFLOW.md skills/ --include="*.md" | grep -v superpowers; python -m unittest discover -s tests -q`
Expected: grep 无输出；测试全绿（代码不引用 skill 目录名）。

```bash
git add -A
git commit -m "refactor: rename read-paper skill to read-source"
```

---

### Task 13: deposit SKILL.md 与 wiki-schema.md 更新

**Files:**
- Modify: `skills/deposit-paper-knowledge/SKILL.md`
- Modify: `skills/deposit-paper-knowledge/references/wiki-schema.md`

- [ ] **Step 1: Update SKILL.md**

frontmatter description 改为：

```yaml
description: Use when the user asks to archive, deposit, preserve, organize, connect, or add a paper report, topic synthesis, source report, or reading notes to PaperWiki, including reports not produced by read-source.
```

Workflow 第 8 步之后追加两步：

```markdown
9. For a topic synthesis (record `kind: topic`), deposit builds the short English graph page at `wiki/topics/<topic_slug>.md`: it links the Chinese synthesis via a vault-qualified wikilink, creates `wiki/sources/` stubs for every studied source, links `entities` (concepts/methods/tools) reciprocally, preserves existing `## Related papers` and `## User notes`, and marks the reading-list entries `deposited` when `list_slug` is set.
10. For a single non-paper source (record `kind: source`), the page lands in `wiki/sources/` with `source_type` and `url` frontmatter; `tools` entities link into `wiki/tools/`.
```

- [ ] **Step 2: Update wiki-schema.md**

`Required collections` 段落改为：

```markdown
Required collections are `papers`, `concepts`, `methods`, `datasets`, and `topics`; `authors`, `sources`, and `tools` are optional. `sources` holds non-paper source pages (frontmatter: `title`, `type: source`, `source_type`, `url`, `source_id`). `tools` holds framework/tool pages (frontmatter: `title`, `type: tool`) describing the tool's role in a harness. Harness design patterns (compaction, hooks, plan-and-execute, ...) live in `methods`. Identity keys extend the paper rule with `url:<sha256-12>` for non-paper sources; the record field name stays `paper_id` for backward compatibility. Use stable lowercase slugs for filenames, readable frontmatter titles, and **short-name** Obsidian `[[stem|Alias]]` wikilinks (Obsidian's default shortest-path form, resolved by note name across the vault) for relationships. Prefer ASCII entity names so filenames stay readable.
```

文末追加：

```markdown
Topic pages built from a topic synthesis contain: `Synthesis report` (vault-qualified link to the Chinese report), `Sources`, `Related knowledge`, optionally `Related papers` (preserved from entity-created pages), and `User notes`. Entity pages created by topic or source deposits use the heading `Related pages`; pages created by paper deposits keep `Related papers`.
```

- [ ] **Step 3: Verify and commit**

Run: `grep -n "sources" skills/deposit-paper-knowledge/references/wiki-schema.md | head -3`
Expected: 能看到新集合说明。

```bash
git add skills/deposit-paper-knowledge
git commit -m "docs: deposit skill covers topic and source kinds; wiki schema adds sources/tools"
```

---

### Task 14: README.md 与 docs/WORKFLOW.md

**Files:**
- Modify: `README.md`
- Modify: `docs/WORKFLOW.md`

- [ ] **Step 1: Update README.md**

管线图（第 5-9 行）替换为：

```text
discover-papers ─┐
                 ├─> read-source ──> deposit-paper-knowledge
ingest-reading-list ──> study-topic ──────────^
       ^                    ^                    ^
  awesome list URL   URL / DOI / PDF     existing report / notes
```

Quick start 代码块末尾追加两行：

```powershell
python paperwiki.py ingest https://github.com/ai-boost/awesome-harness-engineering --list-slug harness-engineering
python paperwiki.py mark harness-engineering url:abc123def456 --status studied
```

Skills 清单替换为：

```markdown
- `discover-papers`: search, normalize, deduplicate, and transparently rank candidates.
- `ingest-reading-list`: sync a curated awesome list into a re-runnable reading list with study states.
- `read-source`: create a structured learning report from a paper, blog post, docs page, or GitHub repo.
- `study-topic`: read several sources on one topic and produce a single Chinese synthesis report.
- `deposit-paper-knowledge`: ingest a report, topic synthesis, or notes into an idempotent linked knowledge base.
```

- [ ] **Step 2: Update docs/WORKFLOW.md**

intent 表替换为：

```markdown
| Intent | Skill | Required input | Output |
| --- | --- | --- | --- |
| Find papers | `discover-papers` | Topic | Ranked records |
| Track a curated list | `ingest-reading-list` | Awesome-list URL or README | `reading-lists/<slug>.json` + diff summary |
| Deep-read one source | `read-source` | URL, DOI, arXiv ID, PDF, repo, or record | Report and reading record |
| Study a topic | `study-topic` | Reading-list section or entry set | Chinese synthesis report + status writeback |
| Preserve knowledge | `deposit-paper-knowledge` | Report, synthesis, or notes | Linked wiki updates |
```

Composition rules 追加三条：

```markdown
- `study-topic` never auto-deposits; personal conclusions come first.
- `ingest-reading-list` re-runs refresh upstream metadata but never overwrite study states.
- Flagship deep reads are suggested by `study-topic` and triggered by the user, never automatically.
```

- [ ] **Step 3: Verify and commit**

Run: `grep -n "read-paper" README.md docs/WORKFLOW.md`
Expected: 无输出。

```bash
git add README.md docs/WORKFLOW.md
git commit -m "docs: workflow contract covers curated-list learning flow"
```

---

### Task 15: 全量验证（CI 对齐）

**Files:** 无新改动；只验证。

- [ ] **Step 1: Run the full suite exactly as CI does**

Run: `python -m unittest discover -s tests -v`
Expected: 全部 PASS，0 failures，0 errors。

- [ ] **Step 2: Byte-compile check（CI 第二步）**

Run: `python -m py_compile paperwiki.py skills/discover-papers/scripts/score_papers.py`
Expected: 无输出、退出码 0。

- [ ] **Step 3: End-to-end smoke（真实 README，联网）**

Run: `python paperwiki.py ingest https://github.com/ai-boost/awesome-harness-engineering --list-slug harness-engineering`
Expected: 输出 JSON 摘要，`total` ≈ 400+，`unparsed_lines` 为空或极少（如有，检查是否为上游格式漂移）。检查 `reading-lists/harness-engineering.json` 各分节条目正确后，把该文件加入提交。

- [ ] **Step 4: Commit the seeded list**

```bash
git add reading-lists/harness-engineering.json
git commit -m "content: seed harness-engineering reading list"
```

---

## Self-review 结论（已在成文时核对）

- **Spec 覆盖**：spec §4.1→Task 1-5、§4.2→Task 11（skill 文档，无 CLI 面）、§4.3→Task 6-7+12、§4.4→Task 8-9+13、§4.5→Task 4-9、§7 测试→各任务 Step 1、§8 文档→Task 10-14、§10 走查→Task 15 Step 3。
- **占位符**：无 TBD/TODO；Task 8 的 `deposit_topic` 占位抛 NotImplementedError 是刻意的任务边界，Task 9 立即替换。
- **类型一致性**：`link_entity(root, collection, name, page_title, page_target, heading=...)`、`mark_list_entries(list_path, source_ids, status, reason=None)`、`merge_reading_list(existing, parsed, now)` 的签名在所有引用处一致；记录字段统一 `paper_id`/`kind`/`source_type`；状态枚举统一 `LIST_STATUSES`。
