# “什么是 Agent Harness”知识积累小实战设计

## 目标

以 `reading-lists/harness-engineering.json` 的 `Foundations` 分区为来源池，完成一次小而完整的 PaperWiki 知识积累实践。最终成果需要让第一次接触 harness 的读者回答：

1. Agent harness 是什么，以及什么不算 harness。
2. Harness、model、agent、agent framework 之间是什么关系。
3. 一个 harness 至少包含哪些运行时组件。
4. Harness 为什么会显著影响可靠性、安全性、成本和长期任务能力。
5. 在一个最小编码任务中，“裸模型调用”和“带 harness 的 agent”如何产生不同执行路径。

本实战同时验证 reading-list 状态机、跨来源专题综合、Obsidian 概念链接和 topic deposit 的幂等性。

## 范围

### 六个核心来源

从 `Foundations` 的 30 条记录中固定选择以下六条，避免阅读过程中随意扩张范围：

1. **Harness Engineering — OpenAI**（`url:f6b93302265d`）：提供 harness engineering 的实践定义和 agent-first 开发背景。
2. **Unrolling the Codex Agent Loop — OpenAI**（`url:ae10eb4597fe`）：提供 agent loop 的运行时分解。
3. **Building Effective Agents — Anthropic**（`url:38c43325a50c`）：界定 workflow、agent 和基础组合原语。
4. **The Anatomy of an Agent Harness — LangChain**（`url:7659f727e260`）：提供 filesystem、code execution、sandbox、memory、context management 等结构视角。
5. **Harness Engineering — Martin Fowler**（`url:33f520c0c534`）：提供 context engineering、architectural constraints、entropy management 的工程视角。
6. **What makes a harness a harness — arXiv:2606.10106**（`arxiv:2606.10106`）：用 agent loop、tool interface、context management、control mechanisms 给出严格的包含判据。

其他 Foundations 条目只列入“刻意未纳入”说明，不作为观点或事实证据。若某一核心来源不可访问，则将其标记为 `blocked` 并在报告中保留证据缺口，不临时换源。

### 不在范围内

- 不实现新的 agent framework 或生产级 harness。
- 不比较所有厂商和开源框架。
- 不深入 memory、compaction、eval、permissions 等单项工程专题；它们只作为 harness 组件出现。
- 不把专题报告拆成六份独立深读报告。
- 不自动把报告标记为 `human_confirmed` 或 `reviewed`。

## 知识模型

专题采用两层互补模型，避免把单一厂商的术语当成通用定义：

### 构成层：运行时必要能力

- **Agent loop**：观察、选择行动、执行、接收反馈并继续。
- **Tool interface**：把外部能力暴露为可理解、可调用、可验证的操作。
- **Context management**：选择、组织、压缩和持久化当前任务需要的信息。
- **Control mechanisms**：权限、预算、终止条件、策略、验证和人工接管。

### 工程层：持续可靠性系统

- **Context engineering**：让 agent 在正确时间看到正确事实和约束。
- **Architectural constraints**：用确定性测试、lint、schema 和结构规则形成反馈。
- **Entropy management**：修复长期任务中的状态、文档和实现漂移。

报告需要明确说明：构成层回答“什么东西有资格称为 harness”，工程层回答“如何让 harness 长期有效”。

## 最小对比案例

使用同一个假想编码任务：“在已有 Python CLI 中增加一个输入校验并保证不破坏旧行为”。不调用外部模型，也不声称进行模型性能实验；这是由六个来源支撑的执行路径分析。

### 裸模型调用

输入只有自然语言需求和少量代码片段。分析其可能缺失的仓库发现、状态持久化、工具反馈、权限边界、回归测试和完成判据，并列出对应失败模式。

### 带 harness 的 agent

按以下路径展开：读取仓库规则和相关文件 → 建立任务状态 → 编辑隔离工作区 → 运行定向测试 → 读取失败反馈并迭代 → 运行全量验证 → 输出可审计结果。每一步标注由哪个 harness 组件提供能力。

对比结果用一张表和一张 Mermaid 流程图表达。结论只讨论可观察的工程机制，不给出未经实验支持的成功率或性能数字。

## 产物

### 专题报告

- `reports/topic-what-is-agent-harness/report.md`
- `reports/topic-what-is-agent-harness/report.html`
- `reports/topic-what-is-agent-harness/record.json`

报告为中文，包含：主题界定、核心问题、两层概念模型、来源观点与证据、最小对比案例、常见误区、实践启发、开放问题、刻意未纳入项和来源清单。每个事实性主张都需要博客/文档标题节、仓库路径或论文页码/章节定位。

### Wiki 入库

- `wiki/topics/agent-harness.md`：英文短标题的图谱入口页。
- `wiki/sources/`：六个来源的身份稳定 stub 页面。
- `wiki/concepts/`：至少关联 Agent Loop、Context Engineering、Control Mechanisms、Entropy Management。
- `wiki/methods/`：至少关联 Deterministic Feedback 和 Harness Decomposition。
- `wiki/tools/`：仅在来源明确把具体产品或框架作为工具讨论时创建；不把厂商名称自动当工具。
- 更新 `index.md` 和 `log.md`。

## 数据流

1. 从 reading list 读取六个固定 `source_id`，确认初始状态。
2. 获取并阅读六个来源，记录选择理由、证据定位和不可访问状态。
3. 生成专题 `report.md` 与权威 `record.json`，渲染 `report.html`。
4. 将成功阅读的来源从 `unread` 更新为 `studied`；不可访问来源更新为 `blocked` 并附原因。
5. 执行 topic deposit，生成 topic/source/entity 双向链接。
6. deposit 只把 reading list 中实时仍为 `studied` 的来源更新为 `deposited`。
7. 再次执行 deposit，验证页面数量、链接数量和人类备注不发生重复或丢失。

## 错误处理

- 页面不可访问、被登录墙阻断或正文不完整：标记 `blocked`，报告证据缺口，不用搜索摘要冒充原文。
- 来源之间定义冲突：分别保留来源观点，再给出明确标记为“综合判断”的解释。
- 论文无法获得可验证全文：不使用只有摘要才能支持不了的严格定义细节。
- `source_id`、状态或 deposit 校验失败：停止后续状态写入，保留可恢复状态并报告失败点。
- HTML 或 wikilink 验证失败：修复 Markdown/record 来源后重新生成，不直接修补派生产物。

## 验收标准

1. 六个来源全部具有 `studied`、`deposited` 或带原因的 `blocked` 状态。
2. 报告能用一句话定义 harness，并能用必要构成判据区分 harness 与 prompt、tool wrapper、model、agent framework。
3. 两层知识模型和最小对比案例均有来源支持，来源观点与综合判断明确分开。
4. `report.md`、`report.html`、`record.json` 三件套完整且相互一致。
5. topic、source、concept、method 页面存在双向链接，没有同名短链接歧义。
6. 第二次 deposit 不新增重复页面或重复链接，并保留预先插入的 `User notes`。
7. 相关测试和全量测试通过，`git diff --check` 无错误。
8. 最终交付时报告具体阅读成功/失败来源、状态变化、生成文件和验证证据，不把生成内容称为人工确认结论。
