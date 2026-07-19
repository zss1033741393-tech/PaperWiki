# Agent Harness 来源主张迁移台账

日期：2026-07-19

目标：把原主题报告直接承载的 18 条来源主张迁移到六份可独立阅读、验证和入库的报告中；主题报告只保留导航与跨来源综合。下表逐条记录去向，确保信息没有因拆分丢失。

| 来源 | 原主题报告中的主张 | 独立报告落点 | 主题报告中的用途 | 状态 |
| --- | --- | --- | --- | --- |
| OpenAI Harness Engineering | 工程师角色转向设计 agent 可执行环境 | `openai-harness-engineering/report.md` → “1. 工程师负责设计可执行环境” | 定义在工程组织中的落地 | 已迁移 |
| OpenAI Harness Engineering | 仓库知识应当本地化、渐进披露且可验证 | 同上 → “2. 仓库知识应是可验证的信息架构” | 共识：上下文需要主动工程化 | 已迁移 |
| OpenAI Harness Engineering | linter、结构测试与熵管理约束高吞吐生成 | 同上 → “4. 架构原则要升级为模型外约束”及“5. 自治会放大已有模式，也需要垃圾回收” | 共识：外部反馈闭环；互补链的维护层 | 已迁移 |
| OpenAI Codex Agent Loop | agent loop 编排推理与工具执行 | `openai-codex-agent-loop/report.md` → “1. Agent loop 是 harness 的运行时核心” | 运行时循环导航；最小案例 | 已迁移 |
| OpenAI Codex Agent Loop | 工具结果与环境变更成为下一轮观察 | 同上 → “1. Agent loop 是 harness 的运行时核心”及“2. 环境变更也是任务输出” | 共识：行动必须进入外部反馈闭环 | 已迁移 |
| OpenAI Codex Agent Loop | compaction 主动管理增长的上下文 | 同上 → “3. 上下文是 harness 主动构造的运行状态”及“4. Compaction 让循环跨越上下文上限” | 共识：上下文需要主动工程化 | 已迁移 |
| Anthropic Building Effective Agents | workflow 与 agent 的区别在控制路径 | `anthropic-building-effective-agents/report.md` → “1. Workflow 与 agent 的差别在控制路径” | 架构边界导航；分歧：分类问题不同 | 已迁移 |
| Anthropic Building Effective Agents | agent 依靠环境真值校准进度并决定停止 | 同上 → “3. Agent 依赖环境真值而不是自我叙述” | 共识：外部反馈闭环 | 已迁移 |
| Anthropic Building Effective Agents | 开放任务适合 agent，但复杂度和风险需受控 | 同上 → “2. 复杂度必须由任务收益证明”及“4. 开放任务适合 agent，但需要 sandbox 与 guardrails” | 架构边界与工程取舍 | 已迁移 |
| LangChain Agent Harness Anatomy | harness 是比单一 loop 更宽的模型外系统 | `langchain-agent-harness-anatomy/report.md` → “1. Harness 是模型之外的系统边界” | 组件解剖导航；分歧：宽边界与构成性边界 | 已迁移 |
| LangChain Agent Harness Anatomy | 文件系统和 Git 承担持久状态与协作 | 同上 → “2. 文件系统承担持久状态与协作表面” | 共识：运行状态不只存在于 prompt | 已迁移 |
| LangChain Agent Harness Anatomy | sandbox、观察工具与测试支持安全执行和自验证 | 同上 → “3. Worktree 不等于 sandbox”及“4. 观察工具与测试构成自验证反馈” | 最小案例与外部反馈闭环 | 已迁移 |
| Fowler Harness Engineering | feedforward 与 feedback 共同构成外层控制 | `fowler-harness-engineering/report.md` → “1. Harness 同时需要事前引导与事后纠偏” | 工程控制系统导航 | 已迁移 |
| Fowler Harness Engineering | 控制可分为计算式与推断式 | 同上 → “2. 控制可以是计算式或推断式” | 四项判据中的控制机制 | 已迁移 |
| Fowler Harness Engineering | 重复失败应升级 steering loop，代码库需具备 harnessability | 同上 → “3. 重复失败应升级 harness”及“5. 代码库的结构决定可 harness 程度” | 互补链的维护层 | 已迁移 |
| What Makes a Harness a Harness | T1—T4 是构成 harness 的四项条件 | `what-makes-a-harness-a-harness/report.md` → “2. 四项条件共同构成成员资格” | 主题定义与四项判据 | 已迁移 |
| What Makes a Harness a Harness | 每项条件都需要可操作阈值 | 同上 → “3. 条件有可操作阈值” | 最小案例的纳入/排除测试 | 已迁移 |
| What Makes a Harness a Harness | 运行时控制区别于 eval；常见组件并非必要条件 | 同上 → “1. Agent harness 的控制发生在任务运行时”及“5. 邻近概念通过失败条件分离” | 分歧：构成性边界；常见误区 | 已迁移 |

## 核对结论

- 18 条原始主张全部有明确的独立报告落点。
- 主题报告不再重复六篇来源的逐篇摘要，而是引用独立报告并组织三组共识、两组分歧和一条互补链。
- 来源证据定位、局限与关系保留在独立报告；主题报告保留概念地图、四项判据、最小对比案例和实践建议。
- 本迁移不改变 `human_confirmed: false`，也不把自动生成内容标记为人工评审完成。
