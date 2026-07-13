# Spec：PaperWiki 三层验证 + HuggingFace 发现源（2026 多智能体协作）

- 日期：2026-07-13
- 状态：设计已定，待用户审阅本 spec
- 分支/工作区：`validation/multi-agent-2026`（独立 git worktree，建议 `../PaperWiki-validation`）

## 1. 背景与目标

PaperWiki 是 `discover → read → deposit` 的可组合论文工作流。本次任务：

- 用**真实 2026 多智能体协作论文**端到端验证项目三大能力：
  1. **发现论文质量是否够高**（discovery quality）
  2. **精读产出是否有品味**（reading taste）
  3. **沉淀 wiki 是否准确**（deposit accuracy）
- 把真实论文**沉淀为可复现的测试用例（冻结 fixtures）**。
- 在独立 worktree 内对项目做**全面而详细的测试**。
- 附带改进（用户决策）：把 HuggingFace 从"纯富集"升级为**一等发现源**。

## 2. 关键现实约束（均为本机实测结论）

| 源 | 状态 | 结论 |
| --- | --- | --- |
| arXiv export API | 429 / 超时 | 本机共享云 IP 被封（环境问题，非工具缺陷） |
| Semantic Scholar | 429 | 匿名常年限流，需 API key |
| Crossref | ✅ 可用 | 返回真实 2026 论文（无需 key） |
| OpenAlex | ✅ 可用 | 返回真实 2026 论文，带引用数 |
| HuggingFace `/papers/search`、`/daily_papers?date=`、`/papers/{arxiv_id}` | ✅ 可用 | 本领域最佳精选源；**可绕过 arXiv IP 封锁**拿到 arXiv 元数据 |
| 浏览器读 `arxiv.org/abs/`、`arxiv.org/html/<id>` | ✅ 可用 | 走另一套基础设施；API 被封时仍能取**全文 HTML**（已实测 golden 例全文可读）|

其他事实：

- vendored 子模块 `paper-craft-skills` **已初始化**（本次拉取）；其 `paper-analyzer` 靠**智能体读 `arxiv.org/html/<id>` 全文** + 6 轮工作流产出深度分析（"品味"引擎），**深度分析不需要 API key**（key 仅用于 comic/poster 的图像生成）。`paperwiki.py` 只做脚手架 + schema 校验 + 渲染；其引用的 `generate_html.py` 在该 pin 版本缺失 → finalize 走内置 HTML 兜底（不阻塞）。
- `discover` 采用**多源合并 + 单源失败可容错**设计：即使 arXiv/S2 双挂，Crossref+OpenAlex+HF 仍能返回真实结果（已实测：8 篇真实 2026 论文）。
- **运行环境**：本次改用 **uv 管理的 Python 3.12** `.venv`（已 gitignore），解除 paper-search-mcp 的 3.10+ 与重依赖限制；`paperwiki.py` 核心仍尽量保持 stdlib-only 以便随处可跑，broader-provider 能力作为环境内的增量层。

**设计后果**：发现走 Crossref+OpenAlex+HF；**精读全文经浏览器读 `arxiv.org/html/<id>`**（可读任意 2026 arXiv 论文，无需传 PDF）；golden 例作品味校准锚点；所有确定性测试离线、可复现。

## 3. 范围

**In scope**

- **uv 管理的 Python 3.12 项目环境**（`.venv`，已 gitignore），装齐 paper-craft / paper-search-mcp 的**合法依赖**。
- 新增 HF 发现源 `huggingface_search` 并接入 `discover` 管线（TDD）。
- 集成 paper-search-mcp 的**合法 provider**：DBLP（CS venue）、Unpaywall / CORE / OpenAIRE / Europe PMC / DOAJ / Zenodo（开放获取全文）等。
- 扩充确定性 pytest 套件（L1）。
- 三大能力证据 rubric（L2）+ LLM-judge（L3）。
- 真实论文 fixtures + 验证结论报告 `REPORT.md`。
- 独立 git worktree。

**Out of scope（YAGNI / 政策）**

- **Sci-Hub（`sci_hub.py`）：不接入、不调用。** 版权规避/盗版源，政策排除；开放获取全文改用 Unpaywall/CORE/OpenAIRE/PMC/arXiv。
- 不改评分权重（除非验证明确发现缺陷，届时单独提议）。
- 不接入需付费 key 的私有 provider（如 IEEE、需 key 的大流量 Semantic Scholar）。

## 4. 架构：三层验证

```
真实 2026 论文 ──▶ 沉淀为「测试用例」(冻结 fixtures) ──▶ 三层验证 ──▶ 结论报告
 (discover 真跑)     discovery / reading / wiki                    ↓
   Crossref                                          ┌────────────┼────────────┐
   OpenAlex                                       L1 确定性     L2 证据       L3 LLM
   HuggingFace(新)                                pytest 引擎   rubric        judge
```

### 4.1 目录结构（worktree 内）

```
validation/
  harvest.py                                 # 一次性真实抓取(记录 query/UTC/每源状态)
  fixtures/
    discovery/multi-agent-2026.json          # 冻结的真实 discover 输出
    reading/<fresh-2026>.analysis.json       # 新发现 2026 论文深读(经浏览器读全文)
    reading/arxiv-2604-03295.analysis.json   # golden 精读(仓库已带,作品味校准锚点)
    wiki/                                     # 冻结的 deposit 结果页
  rubrics/
    discovery-quality.md
    reading-taste.md
    wiki-accuracy.md
  judge/
    judge.py                                  # LLM-judge 结构化打分(无 key 时降级)
    prompts/*.md
    scores/*.json
  REPORT.md                                   # 三大能力 PASS/PARTIAL/FAIL 结论
tests/
  test_scoring.py            # 扩充:band 阈值/coverage 重归一/缺失信号/越界/引用对数化/时效/撤稿flag
  test_identity_merge.py     # DOI 优先/arXiv 版本/跨源别名/标题哈希/冲突保留
  test_discover_integration.py  # monkeypatch fetch,含 arXiv-429 容错
  test_huggingface_source.py    # 新 HF 发现源(归一化/2026过滤/去重)
  test_finalize.py           # schema 必填校验/MD+HTML/状态流转/mermaid 兜底
  test_deposit.py            # 幂等/双向链接/笔记保全/index+log
  test_recommend.py          # 去重/查询派生
  test_errors.py             # .paperwiki/errors.jsonl 落盘
```

### 4.2 HuggingFace 发现源（新功能）

- 新函数 `huggingface_search(query, limit)`：
  - 主走 `/papers/search?q=<query>` 取候选；可选 `/daily_papers?date=<2026 日期>` 补精选。
  - 归一化到 `paper-record` schema：`title/authors/abstract/year/arxiv_id/source_url(hf)/pdf_url(arxiv)/hf_upvotes/github_url/hf_ai_summary/provenance(provider=huggingface-search)`。
  - `year` 推断：优先接口字段；否则由 arXiv id 前缀推断（`26xx` → 2026）。
  - 2026 过滤：arXiv id 前缀 `26` 或 `year>=2026`。
- 接入 `cmd_discover` 的 provider 列表（第 5 个），沿用单源失败可容错。
- 与现有 `huggingface_enrich` 的关系：search 结果已带 upvotes/github → 跳过对其重复 enrich；enrich 仍服务于"非 HF 来源但有 arxiv_id"的记录。避免重复 provenance。
- 评分影响：`novelty`（HF upvotes）信号能覆盖更多记录 → `coverage` 提升、置信度调整更充分。
- 守则（沿用现有注释）：HF upvotes 是**社区兴趣**，不等于学术质量。

### 4.2b paper-search-mcp 合法 provider 集成

uv 环境装齐依赖后，paper-search-mcp（~24 个合法源）可用。本次接入价值最高的：

- **DBLP**：权威 CS 会议/期刊 venue 数据 → 校正 venue 信号噪声（如"Asian Journal…"错配）；无摘要，靠 `merge` 与 OpenAlex/Crossref 互补。
- **Unpaywall / CORE / OpenAIRE / Europe PMC / DOAJ / Zenodo**：**开放获取全文/PDF** 发现 → 非 arXiv 论文也能合法取全文。
- 通过其 platform 类直接调用；结果归一化进现有 `merge`/`score` 管线，单源失败可容错。
- **Sci-Hub 明确排除**（见 Out of scope）：版权规避源，不接入、不调用。

### 4.3 L1 确定性引擎测试（离线 / 可 CI）

从现有 9 个测试扩到全面覆盖。所有测试 **monkeypatch 网络（`paperwiki.fetch`）**，零真实调用：

- **评分**：`must-read/recommended/candidate/watch` band 阈值；coverage 重归一；缺失信号处理；越界报错；引用 `log1p` 归一；时效衰减；撤稿/撤回 flag；HF upvotes novelty。
- **身份/合并**：DOI 优先；arXiv 版本号归一；跨源别名合并；标题哈希兜底；冲突值保留。
- **discover 集成**：模拟 arXiv/S2 抛错 → 断言"survivors 仍返回 + 错误被记录"（复刻真实 429 场景）；`since-years` 截断；输出结构。
- **finalize**：analysis 缺字段 → 报错；生成 MD+HTML；状态 `reading→reviewed`；mermaid 兜底。
- **deposit**：重跑幂等（1 页）；概念/方法/数据集/主题双向链接；user notes 保全；`index.md`/`log.md` 更新。
- **recommend**：与已有 wiki 页去重；查询派生。
- **错误**：命令失败 append `.paperwiki/errors.jsonl`。

### 4.4 L2 证据 rubric（对真实用例，逐条 pass / partial / fail + 证据锚点）

三张 rubric，每条 criterion 标注"是否机械可测 / 判定方法 / 证据锚点"。

**发现质量**
- 切题性：must-read/recommended 的 relevance ≥ 阈值且主题词命中标题。
- 噪声抑制：泛化综述/离题项不进 must-read（实例：1418 引用的泛 LLM 综述被正确压到 candidate）。
- 排序正确：结果按 score 单调；band 阈值一致。
- 容错召回：arXiv/S2 失败时仍返回 ≥5 篇真实相关论文（已实测返回 8 篇）。
- 证据透明：每篇含 `signals/coverage/reasons/missing_evidence`。

**精读品味**
- 忠实：每条 `findings/experiments` 有页/节 evidence 锚点；venue/数字不杜撰（对照源）。
- 洞见：tldr 有信息量；contributions/open_questions 非套话。
- 完整：schema 各节非灌水占位。
- 可视：mermaid 反映真实方法流。
- 分离：paper claims / 解释 / user notes 三者分离。

**wiki 准确**
- 双向链接：paper ↔ concept/method/dataset/topic 互指。
- 一致：wiki 实体 = analysis 抽取实体。
- 幂等：重跑 deposit → 仍 1 页，user notes 保全。
- 台账：`index.md`/`log.md` 更新。
- 无静默覆盖：冲突保留。

### 4.5 L3 LLM-judge

- `judge.py`：输入（论文源文本摘录 + 工具输出 + rubric），输出结构化 `{dimension: {score 1-5, rationale, evidence}}`。
- 维度：发现相关性、精读品味（忠实 / 洞见 / 完整）。
- 校准锚点：golden `2604.03295` 分析设为高分参照。
- 执行：主用**会话内 Claude 结构化评审**，可复现地把 prompt+输出落 `judge/scores/*.json`；附**可选 Anthropic API 版**（读 `ANTHROPIC_API_KEY`，缺失则跳过并说明）。
- 定位：judge 是**辅助信号**，不覆盖 L2 机械判定。

### 4.6 结论报告 `REPORT.md`

- 每能力：**PASS / PARTIAL / FAIL** + 证据（数字、实例、对应 L1/L2/L3 结果）。
- 附：pytest 全绿输出、rubric 勾选表、judge 分数表、已知局限（arXiv/S2 封锁、全文获取限制）。

## 5. 数据流

```
discover(live: crossref+openalex+HF) → 冻结 discovery fixture
  → read(浏览器读 arxiv.org/html 全文的新 2026 论文 + golden 2604.03295 锚点) → finalize → deposit(隔离 vault)
  → 冻结 wiki fixture → L1/L2/L3 跑在 fixtures 上 → REPORT.md
```

## 6. 可复现与错误处理

- `harvest.py` 记录 query、UTC 时间、每 provider 状态（成功/429/超时），让"某源为何缺失"可解释。
- 所有 L1 测试离线；live harvest 一次性，产物入库。
- 失败落 `.paperwiki/errors.jsonl`（现有机制）。

## 7. 测试策略

- **TDD**：HF 源与每个引擎增强，先写测试再实现。
- **verification-before-completion**：REPORT 每条 PASS 必须有命令输出/文件证据支撑。
- 通过标准：`python -m unittest discover -s tests -v` 全绿 + `python -m py_compile paperwiki.py`。

## 8. 里程碑

1. 建 worktree + 骨架（含本 spec 提交到分支）；建 **uv Python 3.12 环境**、装合法依赖、初始化 `paper-craft` 与 `paper-search-mcp` 子模块。
2. TDD 加 HF 发现源 + paper-search-mcp 合法 provider（DBLP/Unpaywall/CORE 等），接入 discover。
3. 扩 L1 引擎测试至全绿。
4. Live harvest → 冻结 discovery fixture。
5. 深读 1 篇新发现 2026 论文（浏览器读 `arxiv.org/html` 全文，走 paper-analyzer 工作流）+ golden 锚点 → finalize/deposit → 冻结 reading/wiki fixture。
6. 写 L2 rubric 并逐条判定。
7. 建 L3 judge 并打分。
8. 汇总 `REPORT.md`，verification 把关。
9. `finishing-a-development-branch` 决定 PR/合并。

## 9. 风险与缓解

- **全文获取**：经浏览器读 `arxiv.org/html/<id>` 已实测可取任意 2026 arXiv 论文全文；仅当某论文无 HTML 渲染版时，才**最后兜底**请用户上传 PDF 到 `inbox/`。
- **Live 波动**：harvest 记录 provider 状态；失败回退仓库样例。
- **LLM-judge 主观**：golden 锚点校准 + 保留 rationale；judge 仅辅助。
- **自测代码**：HF 源自己写自己测 → 用 TDD + 独立 fixture 缓解；报告区分 baseline / improved。
