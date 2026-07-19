# Agent Harness 双层报告入库实施计划

日期：2026-07-19
状态：已完成
目标分支：`codex/pr-5-review-fixes`
目标 PR：`zss1033741393-tech/PaperWiki#5`

## 1. 目标

把当前“6 个来源直接汇总为 1 份主题报告”的流程升级为双层知识产物：

1. 每个入选来源先生成一份可独立阅读、可独立校验、可独立入库的来源报告。
2. 主题报告只负责跨来源综合：统一定义、概念地图、共识与分歧、模式比较和实践案例。
3. 主题综合必须显式绑定其依赖的来源报告；来源报告缺失、身份不一致或在综合后发生变化时，主题包校验失败。
4. 保持来源身份、阅读列表状态、图谱链接和人工确认状态一致，不把生成内容误标为人工评审完成。

本计划不依赖 Superpowers Skills。

## 2. 最终产物

### 2.1 六份独立报告

| 来源身份 | 类型 | 报告目录 |
|---|---|---|
| `url:f6b93302265d` | blog/source | `reports/openai-harness-engineering/` |
| `url:ae10eb4597fe` | blog/source | `reports/openai-codex-agent-loop/` |
| `url:38c43325a50c` | blog/source | `reports/anthropic-building-effective-agents/` |
| `url:7659f727e260` | blog/source | `reports/langchain-agent-harness-anatomy/` |
| `url:33f520c0c534` | blog/source | `reports/fowler-harness-engineering/` |
| `arxiv:2606.10106` | paper | `reports/what-makes-a-harness-a-harness/` |

每个目录必须包含：

- `report.md`：人工可读的规范正文，作为长文唯一事实源。
- `report.html`：只由对应 `report.md` 重建。
- `analysis.json`：结构化分析数据。
- `record.json`：来源身份、来源类型、状态、URL、实体和报告路径。

五篇网页文章使用 `kind: source`；arXiv 论文保持 `kind: paper`，不伪装成博客来源。

### 2.2 一份主题综合报告

保留现有目录：

`reports/topic-what-is-agent-harness/`

主题报告继续保留：

- Harness、Model、Agent、Framework 的边界。
- 四项构成判据。
- 概念地图。
- 最小 Python CLI 对比案例。
- 八维对照表。
- 跨来源共识、分歧、互补关系和开放问题。

主题报告不再承担六篇文章的完整逐篇解读。每个来源只保留“角色摘要 + 独立报告链接 + 必要的一手证据定位”；完整论证结构、局限和逐条证据进入对应来源报告。

## 3. 数据契约调整

### 3.1 来源报告内容契约

每份来源报告至少包含以下章节：

1. 来源信息与阅读范围。
2. 问题与背景。
3. 论证结构。
4. 关键观点与证据。
5. 核心概念与方法。
6. 局限与适用边界。
7. 对 Agent Harness 主题的贡献。
8. 与其他五个来源的关系。
9. User notes。

写作规则：

- 明确标记“来源观点”“综合解释”“开放推断”。
- 网页使用全文绝对 H2 序号加段落、列表或表格位置。
- 论文使用章节、表格、图和 PDF 页码。
- 每条关键观点都必须有可复现定位，不能使用“相关部分”“附近”“随后”等相对措辞。
- 不从现有主题报告机械切块；必须重新打开原文核对上下文。
- `human_confirmed: false`，除非用户明确逐份确认。

### 3.2 `analysis.json` 扩展

沿用现有 paper/source 分析字段，并为主题依赖补充：

- `evidence`：结构化证据定位列表。
- `topic_contribution`：该来源对 Agent Harness 主题提供的独特贡献。
- `relations`：与其他来源的支持、补充或冲突关系。

这些字段可作为通用 read-source 能力的可选字段，但在 `source_reports_required: true` 的主题包中必须存在且非空。

### 3.3 主题 `record.json` 扩展

新增顶层字段：

```json
{
  "source_reports_required": true
}
```

每个 `sources[]` 项新增：

```json
{
  "report_path": "reports/openai-harness-engineering/report.md",
  "report_kind": "source",
  "report_sha256": "..."
}
```

约束：

- `source_id` 必须与来源报告 `record.json` 的 `paper_id` 完全相同。
- `report_kind` 必须与来源报告类型一致。
- `report_path` 必须位于仓库 `reports/<slug>/report.md`。
- `report_sha256` 绑定主题综合时使用的来源报告版本；来源报告改变后必须重新综合或重新确认绑定。
- 六个 `report_path` 必须唯一，避免同名文章发生目录碰撞。

## 4. 代码实施

### 阶段 A：建立主题包验证器（TDD）

先在 `tests/test_topic_bundle.py` 写失败测试，再实现：

`python paperwiki.py validate-topic reports/topic-what-is-agent-harness/report.md --root .`

验证器检查：

- 主题记录声明需要独立来源报告。
- 所有来源均有可解析的 `report_path`。
- 主题 `source_id` 与来源 `record.json` 身份一致。
- `report_kind`、URL、标题和来源类型不发生静默漂移。
- `report.md`、`report.html`、`analysis.json`、`record.json` 四件套齐全。
- SHA-256 与主题记录绑定值一致。
- 来源报告不是初始 scaffold，关键结构化字段非空。
- `human_confirmed` 未被自动设为 true。
- 六个来源身份和报告路径均唯一。

首轮 RED 用例：

1. 缺少来源报告时失败。
2. `source_id` 不一致时失败。
3. 同一路径绑定两个来源时失败。
4. 来源报告修改后摘要失效时失败。
5. 缺少 `analysis.json` 或 HTML 时失败。
6. 五个 source 加一个 paper 的合法混合主题包通过。

### 阶段 B：修复混合来源图谱入库（TDD）

当前 `deposit_topic` 会把所有主题来源都写到 `wiki/sources/`，导致 arXiv 论文也成为 source stub。新增失败测试后修改为：

- `report_kind: source` 链接 `wiki/sources/<source-id>.md`。
- `report_kind: paper` 链接 `wiki/papers/<paper-id>.md`。
- 已存在深读页面时只幂等追加主题反向链接，不用薄 stub 覆盖完整正文。
- 旧主题记录没有 `report_path` 时保持兼容的 stub 行为。
- 新主题记录声明 `source_reports_required: true` 时，不允许回退到 stub。

需要覆盖的回归测试：

1. 论文来源不会同时生成 source 和 paper 两个身份节点。
2. 两篇同名 Harness Engineering 仍以 source ID 分离。
3. 来源页面和主题页面的双向链接各出现一次。
4. 重复 deposit 不重复实体、链接或 User notes。
5. 已有人工笔记和相关页面不丢失。

### 阶段 C：更新主题学习流程

修改 `skills/study-topic/SKILL.md`：

1. 选定来源后，先逐个执行单来源深读。
2. 六份来源报告全部通过门禁后，才能写主题综合。
3. 主题综合从来源报告提取比较维度，但涉及事实时仍保留一手来源定位。
4. 主题记录必须绑定报告路径和摘要。
5. 任一来源 blocked 时保留失败状态；不得用缺失报告的薄摘要冒充完成。
6. 不自动 deposit；只有整个主题包验证通过后才进入入库阶段。

同步更新 `skills/read-source/SKILL.md`，明确博客、文档、仓库和论文都可以成为主题包的独立来源报告，并采用中性的“来源信息”模板，避免把工程博客写成“论文实验”。

### 阶段 D：生成六份来源报告

按来源逐份执行，不能并行写同一主题记录：

1. 创建规范目录和四件套。
2. 重新打开完整原文。
3. 将现有主题报告中的 18 条来源观点作为迁移清单，而不是唯一材料。
4. 补齐文章结构、关键证据、局限、主题贡献和来源关系。
5. 运行 finalize/render、报告 verifier 和聚焦测试。
6. 单份报告通过后再进入下一份。

建议顺序：

1. OpenAI Harness Engineering：工程角色与仓库环境。
2. OpenAI Codex Agent Loop：运行时闭环。
3. Anthropic Building Effective Agents：workflow/agent 边界。
4. LangChain Anatomy：组件解剖与宽边界定义。
5. Fowler Harness Engineering：前馈/反馈工程系统。
6. arXiv:2606.10106：必要与充分条件，作为定义锚点。

### 阶段 E：重构主题综合

1. 建立“旧报告观点 → 新来源报告章节”的迁移台账，保证现有 18 条核心来源观点不丢失。
2. 将逐篇长段落改成六条来源导航，每条包含角色、独立报告链接和一句主题贡献。
3. 把真正跨来源的比较保留在主题报告：
   - 至少三组共识。
   - 至少两组边界差异或术语分歧。
   - 至少一组互补关系。
4. 保留概念地图、四项判据、最小案例和八维比较。
5. 更新主题 `record.json` 的报告绑定和 SHA-256。
6. 由 Markdown 重建主题 HTML。

### 阶段 F：迁移并重新入库

入库顺序固定为：

1. 五份网页来源报告。
2. 一份论文报告。
3. 主题综合报告。

迁移当前 arXiv source stub 前，先确认它只包含生成元数据和 Agent Harness 反向链接；创建并验证 `wiki/papers/arxiv-2606-10106.md` 后，再移除旧的 `wiki/sources/arxiv-2606-10106.md`，避免双身份节点。

状态规则：

- 当前六个 reading-list 条目已经是 `deposited`，迁移过程不得降级为 `studied` 或 `reading`。
- 六份报告和记录最终均为 `deposited`。
- `human_confirmed` 保持 false。
- 不写入 `reviewed`，除非用户明确确认。

## 5. 验收标准

### 5.1 结构验收

- 恰好 6 份独立来源报告和 1 份主题综合报告。
- 7 个目录均有 `report.md`、`report.html`、`record.json`；六份来源另有 `analysis.json`。
- 主题记录的六个 `source_id`、路径、类型和摘要全部通过 `validate-topic`。
- 两篇同名 Harness Engineering 的目录、ID 和图谱页面互不冲突。

### 5.2 内容验收

每份来源报告必须满足：

- 至少 3 条关键观点。
- 每条观点都有确定性定位。
- 至少 2 个不同证据位置。
- 明确写出局限与适用边界。
- 明确写出对 Agent Harness 主题的独特贡献。
- 明确区分来源观点和综合解释。
- 没有无法由原文支持的事实。

主题报告必须满足：

- 六个独立报告均有可点击链接。
- 逐篇内容只作导航，不重复完整来源报告。
- 原有 18 条核心观点在迁移台账中均有去向。
- 概念地图、四项判据、八维对照和最小案例仍存在。
- 至少包含 3 组跨来源共识、2 组差异和 1 组互补关系。

### 5.3 图谱与状态验收

- 这六个身份最终对应 5 个 `wiki/sources` 页面和 1 个 `wiki/papers` 页面。
- 不存在 `wiki/sources/arxiv-2606-10106.md` 与 paper 页面并存的重复身份。
- 每个来源/论文页面到 Agent Harness 主题的反向链接恰好一次。
- 主题、概念、方法和来源链接双向可达。
- 六个 reading-list 状态仍为 `deposited`。
- 所有报告保持 `human_confirmed: false`。

### 5.4 自动化验收

必须全部通过：

```powershell
python paperwiki.py validate-topic reports/topic-what-is-agent-harness/report.md --root .
python -m unittest tests.test_topic_bundle tests.test_deposit_kinds tests.test_finalize tests.test_verify_report
python -m unittest discover -s tests
python -m py_compile paperwiki.py skills/read-source/scripts/verify_report.py
git diff --check
```

对 7 份报告逐一执行：

```powershell
python skills/read-source/scripts/verify_report.py <report.md>
```

然后重新渲染全部 HTML，并确认重建后 Git 无意外差异。

### 5.5 浏览器验收

对全部 7 份 HTML 做自动 DOM 检查：

- `.katex-error` 数量为 0。
- 可见原始 `$$` 数量为 0。
- 页面横向溢出元素数量为 0。
- Mermaid 容器都生成 SVG。

人工抽查至少三类页面：

1. 一篇网页来源报告。
2. 包含论文证据或公式的 arXiv 报告。
3. 包含概念地图和对照表的主题综合报告。

### 5.6 幂等性验收

第一次完成入库后记录所有实质产物 SHA-256；再次按相同顺序 deposit：

- 7 份报告、图谱页面、阅读列表和索引字节级不变。
- 不重复插入链接、实体或 User notes。
- 只允许操作日志追加真实的新 deposit 事件。

## 6. 提交与评审切分

建议按以下边界提交，便于 PR 审查：

1. `test: define topic bundle report contract`
2. `feat: validate standalone reports for topic synthesis`
3. `fix: deposit mixed source and paper topic references`
4. `docs: require source reports before topic synthesis`
5. `docs: add six agent harness source reports`
6. `docs: rebase agent harness synthesis on source reports`
7. `docs: redeposit agent harness report bundle`

最终评审关注：

- 数据契约是否兼容旧主题记录。
- 来源身份是否唯一。
- 主题报告是否真正做综合，而非再次拼接六篇摘要。
- TDD 测试是否覆盖失败路径，而不只覆盖成功样例。
- 报告门禁、完整测试、浏览器检查和幂等性证据是否齐全。

## 7. 完成定义

只有当以下条件同时满足，才能声称新版入库完成：

1. 六份来源报告与一份主题报告全部存在并通过各自门禁。
2. `validate-topic` 成功，且来源报告摘要没有过期。
3. 混合 source/paper 图谱不存在重复身份。
4. 聚焦测试与完整测试全部通过。
5. 浏览器渲染与幂等性验证通过。
6. PR 中清楚说明修改内容、迁移影响、验证命令和未解决事项。
7. 未擅自设置人工评审完成状态。
