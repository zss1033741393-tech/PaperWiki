---
paper_id: url:7659f727e260
status: deposited
source: https://blog.langchain.com/the-anatomy-of-an-agent-harness/
generated: true
human_confirmed: false
---

# LangChain《The Anatomy of an Agent Harness》来源报告

> **一句话结论：**harness 是模型之外把智能转化为可持续工作的系统层，涵盖提示、工具、执行环境、状态、编排和确定性 hooks，并应从期望行为反推所需组件。

## 来源信息与阅读范围

- 来源：LangChain Blog，Vivek Trivedy，2026-03-10。
- 原始 URL：https://blog.langchain.com/the-anatomy-of-an-agent-harness/
- 当前规范 URL：https://www.langchain.com/blog/the-anatomy-of-an-agent-harness
- 阅读范围：正文 12 个 H2 小节，包含 Key Takeaways；重点核对边界、文件系统、sandbox、验证和长时任务。

## 问题与背景

文章从“模型原生不能长期持有状态、执行代码、访问实时知识或配置环境”出发，主张不要把 agent 能力全部归因于模型。期望的产品行为必须被翻译为模型之外的具体系统能力，这些能力共同构成 harness。

## 论证结构

文章先采用一个宽边界定义，把模型之外的代码、配置和执行逻辑纳入 harness；再从模型能力缺口反推文件系统、Git、bash、sandbox、浏览器、测试、记忆和搜索等组件；随后说明长时任务需要这些原语组合；最后讨论模型训练与 harness 设计的耦合以及动态组装工具和上下文的未来方向。

## 关键观点与证据

### 1. Harness 是模型之外的系统边界

**来源观点：**作者把系统提示、工具、skills、MCP、文件系统、sandbox、浏览器、编排逻辑以及 compaction、continuation、lint 等 deterministic hooks 都放进 harness。这个定义强调围绕模型智能设计系统，而不是只列一个 agent loop。

[定位：全文 H2 #2（harness 边界），第 1—4 段及第 1 个列表]

### 2. 文件系统承担持久状态与协作表面

**来源观点：**文件系统使 agent 可以读取真实工作数据、把中间结果移出 context window、跨 session 保留状态，并让多 agent 与人类通过共享文件协作；Git 又增加历史、差异和恢复能力。

[定位：全文 H2 #5（持久存储与上下文管理），第 1—5 段及第 1 个列表]

### 3. Worktree 不等于 sandbox

**来源观点：**sandbox 为 agent 生成代码提供隔离执行环境，并可限制命令和网络；它同时支持按需创建和销毁环境。Git/worktree 主要组织 checkout 与版本状态，不能替代进程、文件系统或网络权限边界。

[定位：全文 H2 #7（安全执行与验证），第 1—3 段]

### 4. 观察工具与测试构成自验证反馈

**来源观点：**浏览器、日志和测试等工具让 agent 观察工作结果；预定义测试可以由 hook 执行并在失败时把错误送回模型，从而形成模型外反馈信号。

[定位：全文 H2 #7（安全执行与验证），第 4—5 段；全文 H2 #10（长时任务），第 4—5 段]

### 5. 长时任务依赖原语组合而非单一超长上下文

**来源观点：**跨多个 context window 的任务需要文件/Git 持久状态、planning、continuation 和 self-verification。每个新上下文通过外部状态恢复目标和进度，而不是保留全部历史 token。

[定位：全文 H2 #10（长时任务），第 1—5 段]

## 核心概念与方法

- **Agent = Model + Harness：**模型提供推理能力，harness 让能力能在环境中工作。
- **Backward Design：**先定义期望行为，再推导所需 harness 功能。
- **Durable State：**把长期状态保存在上下文窗之外的文件和版本记录中。
- **Safe Execution：**通过 sandbox、命令 allow-list 和网络隔离控制代码执行。
- **Self-verification：**让测试和观察工具生成可纠正行动的外部反馈。
- **Just-in-time Assembly：**未来按任务动态选择工具和上下文，而不是固定预装全部能力。

## 局限与适用边界

- “模型之外全部代码与配置”是刻意采用的宽边界，比四项构成性成员测试更包容。
- 文章来自 harness 工具供应商，组件选择与 deepagents 产品方向存在关联。
- 组件列表说明“可以包含什么”，不能单独证明“必须包含什么”。
- 文中 benchmark 例子提示 harness 影响性能，但没有控制模型变量的系统实验。

## 对 Agent Harness 主题的贡献

本文提供最完整的组件解剖和从行为反推能力的方法。它帮助主题报告把抽象四项判据落实为文件系统、Git、sandbox、浏览器、测试、hooks、planning 和 memory 等可实现部件，同时提醒“构成性核心”与“成熟度组件”不能混为一谈。

## 与其他来源的关系

- 扩展 [[reports/openai-codex-agent-loop/report|OpenAI Codex Agent Loop]]：从循环协议扩展到状态、执行和长时任务组件。
- 与 [[reports/openai-harness-engineering/report|OpenAI Harness Engineering]] 相互印证文件/Git、可观察性和测试反馈，但本文更偏产品组件清单。
- 受到 [[reports/anthropic-building-effective-agents/report|Anthropic Building Effective Agents]] 的复杂度原则约束：并非任务都需要完整组件集。
- 边界宽于 [[reports/what-makes-a-harness-a-harness/report|What Makes a Harness a Harness]]；后者只把 loop、tools、context、control 视为成员条件。

## User notes
