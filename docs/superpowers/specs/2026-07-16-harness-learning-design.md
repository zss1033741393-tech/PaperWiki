# Spec：Curated List 学习流 —— 从 awesome-harness-engineering 沉淀 harness 工程知识

- 日期：2026-07-16
- 状态：设计已获用户认可，待用户审阅本 spec
- 分支：`claude/harness-engineering-wiki-e3c03e`

## 1. 背景与目标

用户要以 [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) 为教材持续学习 harness engineering，并把知识沉淀进 PaperWiki。

该仓库的构成（2026-07-16 快照）：416 个条目，约 183 条 GitHub 仓库、约 170 条工程博客与官方文档（Anthropic、LangChain、OpenAI、Google、Microsoft 等）、61 条 arXiv 论文；按问题域组织为分类树 —— Foundations、12 个 Design Primitives（Agent Loop、Planning、Context Delivery & Compaction、Tool Design、Skills & MCP、Permissions、Memory & State、Orchestration、Verification & CI、Observability、Debugging & DX、Human-in-the-Loop）、Reference Implementations、Security & Sandbox、Evals、Templates、Production Infrastructure & Operations。

现状矛盾：PaperWiki 是纯论文架构 —— 身份识别依赖 DOI/arXiv ID/标题哈希，`analysis.json` 要求页码/图表证据，打分使用学术信号，wiki 必需集合为 papers/concepts/methods/datasets/topics。约 85% 的目标内容（博客、仓库、文档）无法进入现有管线。

目标：新增一条**清单驱动**的学习流（与搜索驱动的 discover 平行），通过**两个新 skill + 两个现有组件泛化**实现，不建平行体系。清单摄取可对任何 awesome list 复用，不与 harness engineering 绑死。

## 2. 已确认的关键决策

| 决策点 | 选择 | 理由 |
| --- | --- | --- |
| 非论文来源建模 | 泛化统一管线：`paper_id` 泛化为 `source_id`（URL 哈希 + `source_type`），read/deposit 扩展接受博客/仓库/文档 | 一套管线、一张图谱；避免两套逻辑长期同步维护 |
| 学习沉淀单位 | 主题综述为主 + 旗舰来源单独精读 | awesome 列表本身按主题分类树组织；400+ 条目逐篇精读不现实 |
| 清单追更 | 可重跑同步：解析 README 落结构化清单，重跑 diff 增量 | 上游持续更新；顺带获得学习进度视图 |
| wiki 分类 | 小幅新增 `wiki/sources/` 与 `wiki/tools/`（可选集合）；设计模式并入现有 `methods/` | 改动可控；论文知识与工程知识留在同一图谱互链 |
| 综述落位与语言 | 沿用双层约定：中文综述报告进 `reports/`，`wiki/topics/` 保持英文短图谱页 | 与现有"reports 中文精读 / wiki 英文图谱"约定一致 |

## 3. 总体架构

```text
                    ┌─ 搜索驱动（现有）: discover-papers ──────────────┐
                    │                                                  ▼
入口层              └─ 清单驱动（新增）: ingest-reading-list ──> reading-lists/<slug>.json
                                                │ 挑主题 / 挑单篇
                    ┌───────────────────────────┴────────────────┐
研读层              study-topic（新增，主题综述）          read-source（read-paper 泛化）
                    reports/topic-<slug>/                  reports/<source-slug>/
                    └───────────────────────────┬────────────────┘
沉淀层              deposit-paper-knowledge（泛化）──> wiki/{topics,methods,tools,sources,...}
```

组合规则沿用 `docs/WORKFLOW.md` 契约并新增三条：

- `study-topic` 不自动 deposit（先留个人结论，与论文流程一致）。
- `ingest-reading-list` 重跑永不覆盖条目的学习状态。
- 旗舰来源精读由 `study-topic` 建议、由用户触发，不自动执行。

## 4. 组件设计

### 4.1 新 skill：`ingest-reading-list`

- 输入：awesome list 的 GitHub URL 或本地 README 路径。
- 解析：`##`/`###` 标题构成 `section_path`；`- [` 行解析为条目 `{title, url, source_type, description}`。`source_type` 枚举：`paper | github | blog | docs | other`。判型按主机名启发式：arxiv.org/doi.org → paper；github.com → github（github.blog → blog）；`docs.*`、`platform.*`、`developers.*`、modelcontextprotocol.io 等文档域名 → docs；其余 http(s) → blog；无法判定 → other。启发式表落在 skill 的 references 里，便于扩充。
- 身份规则（全局统一，供清单、report、wiki 三层对齐）：
  - 有 arXiv ID → `arxiv:<id>`（忽略版本后缀）；
  - 有 DOI → `doi:<小写 doi>`；
  - 否则 → `url:<sha256 前 12 位>`，URL 规范化：统一 https、去尾斜杠、去 utm 等跟踪参数、域名小写。
- 输出：`reading-lists/<list-slug>.json`，schema 为新文件 `skills/ingest-reading-list/references/reading-list.schema.json`。顶层字段：`list_slug`、`source_repo`、`retrieved_at`、`entries[]`。条目字段：`source_id`、`title`、`url`、`source_type`、`section_path[]`、`description`、`added_at`、`status`、`status_updated_at`、可选 `notes`、可选 `blocked_reason`、可选 `removed_upstream`。
- 学习状态机：`unread → queued → skimmed → studied → deposited`；`blocked` 可从任意状态进入且必须带 `blocked_reason`。状态由 ingest 初始化为 `unread`，之后由 study/deposit 流程回写（`queued`/`skimmed` 也可由用户手动标记）；ingest 重跑永不改动状态字段。
- 重跑 diff 语义：
  - 新增（新 `source_id`）→ 追加为 `unread` 并在摘要中列出；
  - 上游移除 → 本地**保留**条目并标 `removed_upstream: true`，不删除；
  - 元数据变更（title/section/description）→ 更新字段、保留状态、在摘要中列出；
  - 无法解析的行 → 记入 diff 摘要，不静默丢弃（应对上游格式漂移）。
- CLI：`python paperwiki.py ingest <url-or-path> --list-slug <slug>`，打印分节统计与 diff 摘要（含各状态计数，即进度视图）。

### 4.2 新 skill：`study-topic`

- 输入：清单中一个分类节点（如 *Context Delivery & Compaction*）或手选条目集合；默认从节点内选 5~8 篇核心资源（奠基文优先 + 各 source_type 代表），选择理由须写入报告。
- 研读：逐篇抓取全文（GitHub 仓库读到 README + docs 层级）；来源观点与个人解读分列；不得虚构；遵守 Obsidian 渲染约定（列表内不用行内 `$` 数学、不用裸 `*`，不使用【】来源标记）。
- 产出（中文综述报告）：`reports/topic-<slug>/report.md` + `record.json` + 可选 `report.html`。
  - `report.md` 结构：主题界定 → 核心问题 → 模式对比 → 各来源观点与证据 → 工具盘点 → 开放问题与实践启发 → 来源清单（含每条状态与选择理由）。frontmatter：`topic_id`、`kind: topic`、`list_slug`、`sources`（source_id 列表）、`status`、`generated: true`、`human_confirmed: false`。
  - `record.json`：`{kind: "topic", topic_slug, title, list_slug, sources: [{source_id, url, role: core|flagship|referenced, status}], created, updated}`。
  - **不产 `analysis.json`**，**不走 `paperwiki.py finalize`**（finalize 依赖 analysis.json，是单源精读的契约）；HTML 用现有 `scripts/render_report.py` 直接渲染。
- 副作用：研读完成后把清单内对应条目状态回写为 `studied`；识别旗舰来源时在报告中**建议**转交 `read-source`，不自动执行。
- 抓取失败的来源：清单条目标 `blocked` 附原因；综述照常推进，引用摘要级信息并明确标注证据缺口。

### 4.3 泛化：`read-paper` → `read-source`

- skill 目录 `skills/read-paper/` 改名为 `skills/read-source/`；description 扩展触发词（博客、文档、仓库精读）；README/WORKFLOW/tests 中引用同步更新。
- 按 `source_type` 分派：
  - **paper**：现有路径逐字节不变（paper-craft 分析器、页码/图表证据、finalize 契约）。
  - **blog/docs**：全文抓取精读；证据定位符放宽为章节/小标题/段落。
  - **github**：README + 文档 + 关键入口代码；证据定位符为文件路径。
- `references/analysis.schema.json` 增加 `source_type` 字段，证据定位符按类型条件校验：paper 至少要求 page 或 section；blog/docs 要求 section/heading；github 要求 path。**论文路径校验保持严格，不因泛化放松。**
- `paperwiki.py read <input>`：按输入自动判型（arXiv/DOI/PDF → paper；github.com → github；其余 URL → blog/docs），脚手架 `reports/<source-slug>/` 与含 `source_type` 的 `record.json`（单源 record 增加 `kind: "source"`，论文保持 `kind` 缺省即 paper 语义，向后兼容）。`finalize` 按 `source_type` 应用条件校验。

### 4.4 泛化：`deposit-paper-knowledge` 与 wiki schema

- 新增两个**可选**集合（必需五集合不动，现有测试不受影响）：
  - `wiki/sources/`：非论文来源页。frontmatter：`title`、`type: source`、`source_type`、`url`、`source_id`；正文含 takeaway、provenance、关联双链。
  - `wiki/tools/`：框架与工具页（LangGraph、TaskWeaver 等）。frontmatter：`title`、`type: tool`、`repo`；正文含定位、在 harness 中的角色、关联模式与来源双链。
- 设计模式（compaction、hooks、plan-and-execute 等）并入现有 `wiki/methods/`（`type: method` 不变）。
- deposit 按 `record.json` 的 `kind` 分派：缺省/`paper` → 现有论文沉淀路径不变；`topic` → 更新 `wiki/topics/<slug>.md`（英文短图谱页，库内限定链接指向中文综述如 `[[reports/topic-context-compaction/report|综述报告]]`），抽取并互链 methods/tools/sources/concepts；`source` → 创建/合并 `wiki/sources/` 页。
- 幂等规则沿用：同 `source_id` 重跑只更新同一页；冲突值保留并加解决任务；照常更新 `index.md`（新集合加入索引分区）与 `log.md`。
- `skills/deposit-paper-knowledge/references/wiki-schema.md` 同步：sources、tools 加入可选集合，写明 frontmatter 契约与短名双链约定。

### 4.5 CLI 变更汇总

| 命令 | 变更 |
| --- | --- |
| `ingest`（新增） | 解析 awesome README → `reading-lists/<slug>.json`，重跑输出 diff 与进度摘要 |
| `read` | 接受任意 URL，自动判 `source_type`，脚手架含类型的 record |
| `finalize` | `analysis.json` 按 `source_type` 条件校验 |
| `deposit` | 按 `record.json` 的 `kind`（paper/topic/source）分派沉淀路径 |
| `discover` / `recommend` | 不变 |

## 5. 目录契约示例

```text
reading-lists/harness-engineering.json        # 清单 + 状态（ingest 维护）
reports/topic-context-compaction/             # 主题综述（study-topic）
  report.md / report.html / record.json
reports/langchain-deep-agents-harness/        # 旗舰源精读（read-source）
  report.md / report.html / analysis.json / record.json
wiki/topics/context-compaction.md             # 英文图谱页（deposit）
wiki/methods/progressive-compaction.md
wiki/tools/llmlingua.md
wiki/sources/anthropic-effective-context-engineering.md
```

清单中的 arXiv 条目身份即 `arxiv:<id>`，与现有论文管线自动汇合：走 read-source 的 paper 路径，沉淀为 `wiki/papers/` 页。

## 6. 错误处理

- 付费墙/404/反爬：条目标 `blocked` 附原因；综述标注证据缺口 —— 符合"失败记录为可恢复状态"契约。
- 上游 README 格式漂移：解析器只依赖 `##/###` 与 `- [` 两个稳定模式；解析失败的行进 diff 摘要。
- 身份冲突（同 URL 换标题/同文多址）：合并证据、保留冲突、加解决任务，沿用 deposit 现有幂等规则。
- 无迁移成本：新集合为可选，存量 wiki 页与 reports 不需改动。

## 7. 测试策略

沿用 pytest + CI（`.github/workflows/ci.yml`）：

- `tests/test_ingest.py`（新）：fixture README（含各 source_type、多级标题、坏行）→ 解析正确性；重跑幂等；新增/移除/变更 diff；状态保留；URL 规范化与 source_id 稳定性。
- `tests/test_deposit.py`（扩展）：topic record 沉淀出 topics 页并链接综述报告；source 页创建与合并；tools/sources 集合出现在 index；重跑幂等。
- `tests/test_finalize.py` / `tests/test_paperwiki.py`（扩展）：`source_type` 条件校验 —— paper 严格不变，blog/github 放宽路径生效；`read` 判型正确。
- 综述内容质量不做自动断言（认知产物），由 SKILL.md guardrails 约束。

## 8. 文档更新清单

- `README.md`：管线图加入 ingest/study 分支；Skills 清单更新（read-source 改名说明）。
- `docs/WORKFLOW.md`：intent 表新增两行（摄取清单 / 主题研读）；组合规则新增第 3 节的三条。
- 新增 `skills/ingest-reading-list/SKILL.md`、`skills/study-topic/SKILL.md`；改名并扩写 `skills/read-source/SKILL.md`；更新 `skills/deposit-paper-knowledge/SKILL.md` 与 `references/wiki-schema.md`。
- 新增 `skills/ingest-reading-list/references/reading-list.schema.json`；更新 `analysis.schema.json`。

## 9. 明确不做（YAGNI）

- 博客/仓库重打分模型：awesome 列表的人工策展即质量信号，分类结构 + 用户挑选即分诊。
- 定时自动同步：手动重跑 `ingest` 即可。
- 间隔重复/测验系统；通用全网爬虫；独立进度命令（进度摘要由 `ingest` 重跑输出兼任）。

## 10. 端到端走查

1. `python paperwiki.py ingest https://github.com/ai-boost/awesome-harness-engineering --list-slug harness-engineering` → 生成 416 条清单，按分类分节，全部 `unread`。
2. 用户："学一下 Context 压缩" → `study-topic` 从 *Context Delivery & Compaction* 节点选出 Anthropic compaction 文档、LangChain Autonomous Context Compression、ACC 论文等约 6 篇 → 产出 `reports/topic-context-compaction/report.md`（中文综述）→ 对应条目状态 `studied`。
3. 用户读综述、写批注，决定精读 LangChain 那篇旗舰博客 → `read-source` 产出 `reports/langchain-deep-agents-harness/`。
4. `deposit` 综述与精读 → 生成/更新 `wiki/topics/context-compaction.md`、`wiki/methods/progressive-compaction.md`、`wiki/tools/llmlingua.md`、若干 `wiki/sources/` 页并互链；条目状态 `deposited`；`index.md`、`log.md` 更新。
5. 下月重跑 `ingest` → diff 报告该节点新增 2 条，进入 `unread` 等待下轮研读。
