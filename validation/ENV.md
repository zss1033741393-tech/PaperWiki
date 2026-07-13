# 验证环境（可复现）

本目录承载 PaperWiki 的三层验证工作，运行在一个 **uv 管理的 Python 3.12 环境**里（`paperwiki.py` 核心仍是 stdlib-only，可脱离本环境运行；本环境只为启用 paper-search-mcp 等 broader-provider 能力）。

## 一次性搭建

```bash
# 在 worktree 根目录
uv venv --python 3.12                              # 建 .venv（uv 自动下载 CPython 3.12）
uv pip install -e vendor/paper-search-mcp pytest   # editable 装 paper-search-mcp + 其合法依赖 + pytest
git submodule update --init vendor/paper-craft-skills vendor/paper-search-mcp
```

- 解释器：`.venv/bin/python` → CPython **3.12.10**（uv 托管）。
- 依赖来源：`vendor/paper-search-mcp/pyproject.toml`（requests / feedparser / fastmcp / pypdf / mcp[cli] / beautifulsoup4 / lxml / httpx）。
- `.venv/` 已在 `.gitignore`，不入库。

## 运行

```bash
.venv/bin/python -m unittest discover -s tests -v   # 确定性引擎测试（L1）
.venv/bin/python -m py_compile paperwiki.py
.venv/bin/python paperwiki.py discover "<topic>" --limit 8 --since-years 1
```

## 本环境的 provider 可用性（实测，2026-07-13）

| Provider | 状态 | 备注 |
| --- | --- | --- |
| Crossref | ✅ | 匿名可用 |
| OpenAlex | ✅ | 匿名可用，带引用数 |
| HuggingFace（search / daily_papers / papers/{id}）| ✅ | 精选源；绕过 arXiv IP 封锁取元数据 |
| 浏览器读 `arxiv.org/html/<id>` | ✅ | 取**全文**用于深读 |
| arXiv export API | ❌ 429 | 共享云 IP 被限流 |
| Semantic Scholar | ❌ 429 | 匿名限流，需 key |
| DBLP（paper-search-mcp）| ⚠️ 503 | dblp.org 暂不可用/波动；管线容错，能用则用 |

**结论**：发现管线在 arXiv/S2/DBLP 波动时，靠 Crossref+OpenAlex+HF 仍返回真实 2026 论文（多源容错设计）。

## 政策边界

- **Sci-Hub（`vendor/paper-search-mcp/.../sci_hub.py`）不接入、不调用**——版权规避/盗版源。开放获取全文改用 **Unpaywall / CORE / OpenAIRE / Europe PMC / PMC / arXiv**。
