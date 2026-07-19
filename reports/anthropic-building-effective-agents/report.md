---
paper_id: url:38c43325a50c
status: deposited
source: https://www.anthropic.com/research/building-effective-agents
generated: true
human_confirmed: false
---

# Anthropic《Building Effective Agents》来源报告

> **一句话结论：**应先区分固定代码路径的 workflow 与由模型动态决定过程的 agent，再根据任务开放度、反馈条件和风险选择最简单的可行架构。

## 来源信息与阅读范围

- 来源：Anthropic Engineering，2024-12-19。
- 原始 URL：https://www.anthropic.com/research/building-effective-agents
- 当前规范 URL：https://www.anthropic.com/engineering/building-effective-agents
- 阅读范围：定义、适用性、构建模式、agents、客户支持与 coding agents 附录。

## 问题与背景

文章针对团队容易过早采用复杂 agent framework 的现象，试图给出一套由简单到复杂的架构选择方法。它把 prompt chaining、routing、parallelization、orchestrator-workers 和 evaluator-optimizer 视为 workflow 模式，再把无法预先硬编码路径的任务交给 agent。

## 论证结构

首先定义 workflow/agent 边界并强调复杂度权衡；随后介绍增强 LLM 和五种可组合 workflow；接着描述 agent 的环境反馈循环、停止方式和适用条件；最后用客服与 coding agents 说明“可行动、可反馈、成功标准清晰”的任务为什么适合 agent。

## 关键观点与证据

### 1. Workflow 与 agent 的差别在控制路径

**来源观点：**workflow 由代码预先规定模型和工具的运行路径；agent 则让模型动态决定过程与工具使用方式。二者都属于广义 agentic systems，但架构控制权不同。

[定位：全文 H2 #1（工作流与智能体定义），第 1 个列表]

### 2. 复杂度必须由任务收益证明

**来源观点：**作者建议先寻找最简单方案，仅在需要时增加 agentic complexity，因为更高自治通常以延迟和成本换取任务表现，并增加错误累积风险。

[定位：全文 H2 #2（何时使用智能体），第 1—2 段]

### 3. Agent 依赖环境真值而不是自我叙述

**来源观点：**agent 在执行期间需要从工具调用或代码执行获得 ground truth，以判断进度；它可以在 checkpoint 或阻碍处返回人类，并可设置最大迭代次数等停止条件。

[定位：全文 H2 #4（构建模式）中 Agents 子节，第 2—3 段]

### 4. 开放任务适合 agent，但需要 sandbox 与 guardrails

**来源观点：**当步骤数量和路径无法预先预测时，动态 agent 更有价值；同时，自治意味着更高成本和复合错误风险，因此需要 sandbox 测试与适当 guardrails。

[定位：全文 H2 #4（构建模式）中 Agents 子节，第 4—5 段]

### 5. 编码任务适合反馈循环，但仍需要人类系统判断

**来源观点：**代码能由自动测试验证，agent 可以用测试结果迭代，输出质量也较易客观测量；但自动测试不能替代对更广系统要求的人类审查。

[定位：全文 H2 #7（Agents in practice）中 Coding agents 子节，第 1 个列表及其后第 1 段]

## 核心概念与方法

- **Workflow：**由预定代码路径编排模型与工具。
- **Agent：**由模型根据当前观察动态决定下一步。
- **Environmental Ground Truth：**来自工具和执行环境、可用于校准进度的外部事实。
- **Evaluator-optimizer：**生成与评价形成迭代反馈，但仍可以是预定 workflow。
- **Orchestrator-workers：**动态分解子任务与综合结果，适用于不可预知的复杂分工。

## 局限与适用边界

- 文章定义的是广义 agentic systems，不直接定义“agent harness”的构成边界。
- 主要证据来自 Anthropic 客户和自身实践，缺少受控比较实验。
- human checkpoint、停止条件和 guardrail 是常见控制模式，不应被误读为每个 agent 的充分定义。
- “简单优先”是架构决策原则，不意味着简单系统一定满足可靠性要求。

## 对 Agent Harness 主题的贡献

本文提供上层架构边界：harness 中可以承载 workflow 或 agent，但只有动态 observation-driven loop 才体现 agent 行为。它还强调 harness 必须把环境反馈和停止控制接入运行过程，而不是只提供工具列表。

## 与其他来源的关系

- 为 [[reports/openai-codex-agent-loop/report|OpenAI Codex Agent Loop]] 提供抽象架构语言；OpenAI 文章则给出具体实现。
- 与 [[reports/fowler-harness-engineering/report|Fowler Harness Engineering]] 一致地强调外部评价和模型外控制。
- 对 [[reports/langchain-agent-harness-anatomy/report|LangChain Anatomy]] 的宽组件列表形成约束：组件数量不是目标，复杂度必须由任务证明。
- 与 [[reports/what-makes-a-harness-a-harness/report|What Makes a Harness a Harness]] 的边界不同：本文区分 workflow/agent，论文进一步区分 harness/framework/SDK/eval harness。

## User notes
