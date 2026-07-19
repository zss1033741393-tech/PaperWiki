---
paper_id: url:ae10eb4597fe
title: "Unrolling the Codex Agent Loop"
status: deposited
type: source
source_type: blog
url: https://openai.com/index/unrolling-the-codex-agent-loop/
source_id: url:ae10eb4597fe
---

# Unrolling the Codex Agent Loop

## Source report

[[reports/openai-codex-agent-loop/report|Unrolling the Codex Agent Loop report]]

## Related knowledge

- [[agent-loop|Agent Loop]]
- [[context-window|Context Window]]
- [[tool-observation|Tool Observation]]
- [[conversation-turn|Conversation Turn]]
- [[context-compaction|Context Compaction]]
- [[tool-result-injection|Tool Result Injection]]
- [[wiki/topics/agent-harness|Agent Harness]]
- [[codex-runtime|Codex Runtime]]
- [[codex-cli|Codex CLI]]
- [[responses-api|Responses API]]


## Generated synthesis (draft)

# OpenAI《Unrolling the Codex Agent Loop》来源报告

> **一句话结论：**Codex harness 的最小运行内核是“模型推理—工具执行—结果写回—再次推理”的循环，并由上下文构造与压缩维持多步任务。

## 来源信息与阅读范围

- 来源：OpenAI Engineering，2026-01-23。
- 原文：https://openai.com/index/unrolling-the-codex-agent-loop/
- 阅读范围：正文 3 个 H2 小节，重点核对 agent loop、Responses API 输入项与 compaction。
- 本文是 Codex CLI 的实现 walkthrough，不是所有 harness 的产品规范。

## 问题与背景

“agent 调用工具”常被简化为一次 function call，但软件 agent 必须把用户输入、系统指令、工具定义、环境结果和历史状态组织成连续回合。文章拆开 Codex CLI 的核心循环，说明模型与 harness 在一次任务中分别负责什么。

## 论证结构

文章先给出抽象循环：模型要么返回最终消息，要么请求工具；harness 执行工具并把结果加入下一次输入。随后进入 Responses API 的 item 模型，说明不同类型的消息、推理与工具结果怎样构成输入。最后讨论状态无关请求的带宽、context window 以及自动 compaction。

## 关键观点与证据

### 1. Agent loop 是 harness 的运行时核心

**来源观点：**Codex harness 负责协调用户、模型与工具。模型提出工具调用时，harness 在环境中执行并把结果追加到输入；新观察改变下一次推理，直到模型返回 assistant message。

[定位：全文 H2 #1（智能体循环），第 2、5—7 段]

### 2. 环境变更也是任务输出

**来源观点：**软件 agent 的主要成果可能已经写入本地文件，而不是只存在于最终自然语言消息。assistant message 更像一个回合的终止信号，控制权随后回到用户。

[定位：全文 H2 #1（智能体循环），第 7 段]

### 3. 上下文是 harness 主动构造的运行状态

**来源观点：**随着工具调用和对话增加，输入会持续增长并竞争有限 context window。上下文管理不是模型内部自然发生的能力，而是 agent loop 的运行职责。

[定位：全文 H2 #1（智能体循环），第 8—10 段]

### 4. Compaction 让循环跨越上下文上限

**来源观点：**Codex 在超过阈值后调用 Responses API 的 compact 端点，用较小的 item 列表替换之前输入；其中包含用于延续模型理解的 compaction item。

[定位：全文 H2 #2（模型推理下的性能考量），第 11—14 段]

## 核心概念与方法

- **Agent Loop：**根据观察反复选择推理、行动或结束。
- **Tool Result as Observation：**工具结果不是日志附件，而是下一轮决策输入。
- **Conversation Turn：**一次用户输入到 assistant message 之间可以包含多轮模型与工具交互。
- **Context Construction：**harness 决定哪些指令、历史、工具和结果进入请求。
- **Compaction：**在保留代表性状态的同时缩小继续运行所需的输入。

## 局限与适用边界

- 文章聚焦 Codex CLI 和 Responses API，工具实现、权限与 sandbox 只被预告，没有完整展开。
- 它说明“循环怎样运行”，但没有提供 harness 的必要充分成员测试。
- 自动 compaction 的存在不等于所有摘要策略都能保留长期任务的因果状态。
- 将 assistant message 作为回合终点是该实现协议，不应直接等同于外部验收完成。

## 对 Agent Harness 主题的贡献

本文为主题提供最清晰的运行时序列：模型提出行动，harness 执行，环境返回观察，观察进入下一轮上下文。它解释了四项构成判据中的 Agent Loop、Tool Interface 与 Context Management 怎样在一次实际调用链中结合。

## 与其他来源的关系

- 与 [[reports/openai-harness-engineering/report|OpenAI Harness Engineering]] 形成内外两层：本文解释一次运行，后者解释仓库环境和长期维护。
- 支持 [[reports/anthropic-building-effective-agents/report|Anthropic Building Effective Agents]] 对“环境反馈循环”的描述，但比后者更具体地展示协议与 item。
- 为 [[reports/what-makes-a-harness-a-harness/report|What Makes a Harness a Harness]] 的 T1—T3 提供产品实现实例；本文自身没有证明 T4。
- 与 [[reports/langchain-agent-harness-anatomy/report|LangChain Anatomy]] 的持久状态和长时任务组件互补。

## User notes



## User notes
