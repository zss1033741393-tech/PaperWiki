---
paper_id: arxiv:2604.18071
status: deposited
source: https://arxiv.org/abs/2604.18071
generated: true
human_confirmed: false
---

# 《Architectural Design Decisions in AI Agent Harnesses》论文报告

> **一句话结论：**这项对 70 个公共 agent 系统的横断面研究把 harness 的工程差异拆成五个反复出现的架构维度，并综合出五类常见设计组合；它适合回答“已经进入 harness 设计空间后该怎样取舍”，不负责严格判定“什么才算 harness”。

## 来源信息与阅读范围

- 作者：Hu Wei。
- 版本：arXiv:2604.18071v1，2026-04-20，cs.AI。
- 原文：https://arxiv.org/abs/2604.18071
- 阅读范围：全文第 1—8 节、表 1—14 及附录中的语料和编码说明。
- 证据冻结点：论文将项目语料冻结在 2026-03-23；本文只复述该横断面快照，不把比例外推为当前生态的永久分布。

## 问题与背景

公开讨论常按知名度、功能清单或单项 benchmark 比较 agent framework，却很少系统解释它们在非 LLM 运行层做了哪些不同的架构承诺。论文研究三个问题：公共 agent 系统反复出现哪些架构决策，这些决策如何共同出现，以及能否据此综合出可供设计者和选择者使用的架构模式。

论文把 “agent harness” 当作围绕模型、负责执行、上下文、工具与控制的非 LLM 工程层的**宽泛工作标签**，并明确说它不是严格的本体定义。因此，它与 arXiv:2606.10106 的关系不是两个相互竞争的定义：后者先做成员测试，本文再比较架构差异。

[定位：第 1 节研究问题与贡献；第 2 节开头对 “agent harness” 的工作定义]

## 论证结构

论文先说明研究协议、70 项目语料、证据来源和编码审计；然后依次统计子代理、上下文、工具、安全和编排五个维度；再用支持度、置信度和提升度描述决策共现；最后把反复出现的组合综合为五种架构模式，讨论选择原则、有效性威胁与未来研究。

## 关键观点与证据

### 1. 五个维度是比较坐标，不是完整本体

**来源观点：**研究以子代理架构、上下文管理、工具系统、安全机制和编排为五个稳定分析维度。作者同时提醒，这五维是对当前语料有分析稳定性的关注点，不是 agent 系统架构的穷尽式本体。

[定位：第 3.3 节编码框架；第 4 节五个结果小节；第 7.3 节 Construct validity]

### 2. 子代理拓扑不能直接读成成熟度阶梯

**来源观点：**70 个项目中，21 个没有子代理，13 个采用 orchestrator-worker，9 个采用 recursive，其他分布在 tool delegation、basic spawn、swarm、event-driven 与 pipeline。论文强调这是一份架构库存，不是从“无子代理”到“群体”的线性成熟度排名。

[定位：第 4.1 节，表 4]

### 3. 上下文设计已经超出狭义“记忆存储”

**来源观点：**hybrid、file-persistent 和 hierarchical 是语料中的主要上下文模式。论文把存储后端、压缩策略、持久范围和 token awareness 一并视为上下文管理；长期任务会迫使系统把上下文处理显式化为子系统，而不只是把历史塞回 prompt。

[定位：第 4.2 节，表 5 及表后四类设计决策]

### 4. 工具扩展能力与执行边界必须一起设计

**来源观点：**显式 registry 是工具注册的众数（24/70，34.3%），MCP-first、插件和企业型方案仍属较小但重要的群体。工具开放程度越高，发现、schema、审批、隔离与审计边界就越不能被当成无关的附加项。

[定位：第 4.3 节，表 6；第 4.4 节，表 7—8]

### 5. 能力增强不等于治理已经跟上

**来源观点：**45% 的项目采用进程分离、31% 使用容器，但 40% 没有明确审计，只有 5% 具有防篡改审计。论文据此指出中间强度隔离常见，而高保证审计罕见。

**精读核验：**论文把 container isolation 与 policy-structured security 的 support 写成 0.89（表 10、12），但按第 3.7/5.1 节给出的定义，support 是 P(A∩B)，不可能超过 container isolation 的边际比例 0.31（表 7）。同样，MCP-first 的边际比例是 0.143（表 6），其与 stronger discovery 的 support 却写成 0.62。0.89 和 0.62 可能实际表示 confidence、内部评分或其他量，但按正文标签无法成立。因此“更强执行与结构化治理共同出现”只能保留为作者报告的描述性方向，不能把这些 support 数字当作已复核证据。

[定位：第 4.4 节，表 7—8；第 5 节共现分析；第 7.2 节分析性猜想]

### 6. 五种模式是“设计组合中心”，不是纯类或排行榜

**来源观点：**论文综合出 lightweight tools、balanced CLI frameworks、multi-agent orchestrators、enterprise full-featured、scenario-verticalized/research-oriented 五种模式。每种模式对应不同复杂度包络与主要权衡；项目归类是主导性分配，不表示类别互斥，也不是统计学习得到的潜在类。

[定位：第 6.1 节综合方法；第 6.2—6.6 节五种模式]

### 7. 选择框架应从目标复杂度包络开始

**来源观点：**个人工具、开发者 CLI、研究编排器和企业平台不需要相同的架构承诺。设计者应先明确是单步辅助、长时工作、多 agent 协调还是生产治理，再选择一致的组件组合，而不是按流行度或逐项堆功能。

[定位：第 7.1 节，特别是 complexity envelope 与 coherent bundles 两项建议]

## 五维架构空间

| 维度 | 核心问题 | 典型权衡 |
|---|---|---|
| 子代理架构 | 是否拆分角色，怎样委派、递归与协调 | 分解能力 vs. 协调成本与可理解性 |
| 上下文管理 | 怎样持久化、压缩、检索并分配 token | 连续性与召回 vs. 基础设施和上下文污染 |
| 工具系统 | 怎样注册、发现、路由和执行能力 | 扩展性与互操作性 vs. 边界复杂度 |
| 安全机制 | 怎样审批、隔离、记录和追责 | 执行自由度 vs. 操作保证与治理成本 |
| 编排 | 谁决定顺序、触发和停止 | 灵活性与并发性 vs. 可预测性和调试难度 |

这五维不能替代 T1—T4。T1—T4 是成员门槛；五维空间用于描述通过门槛之后的实现位置与工程取舍。

## 五种架构模式

1. **Lightweight Tools：**最小循环、内存上下文、硬编码工具和弱隔离；部署轻，但不适合长时状态与复杂协调。
2. **Balanced CLI Frameworks：**基础委派、文件持久化、MCP 或装饰器注册、进程隔离；适合开发工具，但治理和深层协调有限。
3. **Multi-Agent Orchestrators：**orchestrator-worker 或递归拓扑、分层/混合上下文、结构化委派、审批与容器/WASM；扩大问题求解范围，也提高理解和控制成本。
4. **Enterprise Full-Featured：**多层子代理、企业记忆、完整扩展生态、多层防御与审计；高保证、高扩展，同时要求更高组织成本。
5. **Scenario-Verticalized / Research-Oriented：**围绕某个研究或垂直目标深挖单一维度，其他维度可能很薄；实验快，但通用性和运营保证有限。

[定位：第 6.2—6.6 节]

## 方法与证据性质

- 研究类型：protocol-guided、source-grounded 的定性实证研究，采用横断面架构比较。
- 语料：70 个公共 agent-system 项目，其中 67 个开源项目、3 个基于公开材料的比较案例；不是 PRISMA 式穷尽调查。
- 证据：仓库源码、目录结构、配置、文档和公开材料；字段保留证据路径。
- 审计：对 15 个项目（21%）做二次人工复核，初始字段级一致率为 94%；没有报告覆盖完整矩阵的机会校正一致性。
- 分析：类别分布、跨维度支持度/置信度/提升度和解释性模式综合；模式不是聚类模型输出。
- 可复现边界：论文公开了 corpus 名单、筛选协议和摘要 codebook，但完整 extraction records、70×字段矩阵、逐字段证据与横向综合被称为 internal audit materials，正文和附录没有给出下载位置。

[定位：第 3.1—3.5 节]

## 局限与适用边界

- 语料偏向能公开观察源码结构的项目，商业闭源、内部企业系统和未公开原型可能处于不同位置。
- 搜索与筛选是系统化但非 PRISMA 的，论文主张分析覆盖而非生态普查。
- 架构编码仍含解释判断，五维框架不是穷尽本体。
- 表 10—12 的两个 support 值高于对应事件的边际比例，无法按论文自己的定义复核；memory、tool discovery 和 security score 的数值量尺也没有在附录 B 定义。
- 完整编码矩阵和逐字段证据未公开，94% 只是 15/70 项目在 consensus 前的 raw field agreement；缺少字段数、分层方式、逐维结果与 κ/α。
- 语料包含多个相关的 `claw-*` 生态项目，没有报告 fork/谱系去重或 cluster sensitivity；70 个项目不能直接当作 70 个独立架构观测。
- 一个代表案例 `claude-code-src` 来自 source-visible leaked snapshot，其真实性、版本与可复核性不同于公开仓库。
- 共现分析不建立因果方向，也没有证明某种模式带来更好的维护性、安全性、采用率或 benchmark 成绩。
- 语料冻结于 2026-03-23，协议采用、安全实践和编排风格会快速变化。

[定位：第 7.3 节 Threats to Validity and Limitations]

## 对 Agent Harness 主题的贡献

arXiv:2606.10106 提供严格的“成员资格层”，本文提供“架构设计空间层”。两者组合并不是简单叠加：本文的纳入条件只要求约 500 LOC 或同等架构足迹，并具有至少一种可观察 infrastructure capability，没有要求 T1—T4 全部成立。若先排除固定 pipeline、机械 context wrapper 或缺少模型独立控制的项目，五维比例、共现与五模式分布都可能改变。当前最稳妥的用法，是把五维当作候选比较坐标，同时把严格筛选后的分布稳定性保留为待验证问题。

## 与其他来源的关系

- 与 [[reports/what-makes-a-harness-a-harness/report|What Makes a Harness a Harness]] 既互补又存在 scope conflict：对方回答“是不是”，本文回答“怎样设计与选择”；但对方的 T1—T4 可能改变本文的经验分母，而不只是增加一个前置标签。
- 为 [[reports/langchain-agent-harness-anatomy/report|LangChain Anatomy]] 的组件清单提供 70 项目横断面的经验分布与组合模式。
- 把 [[reports/anthropic-building-effective-agents/report|Anthropic Building Effective Agents]] 的“从简单方案开始”落实为 complexity envelope 与五类设计组合。
- 为 [[reports/fowler-harness-engineering/report|Fowler Harness Engineering]] 的控制观点补充隔离和审计分布，但不把共现误写成因果收益。
- 可将 [[reports/openai-codex-agent-loop/report|OpenAI Codex Agent Loop]] 视为运行内核案例，再用五维检查其外围上下文、工具、安全和编排选择。

## 开放问题

- 用严格 T1—T4 重新筛选这 70 个系统后，五维分布和五种模式是否仍稳定？
- 哪些设计组合与维护性、安全事件、任务成功率或采用率存在可复现关联？
- 架构模式如何随项目从轻量工具演进到平台而发生纵向迁移？
- 怎样用多编码者、共享 codebook 和机会校正一致性提高分类可复现性？
- 表 10—12 的 0.62、0.73、0.89 实际对应 support、confidence 还是内部综合评分？
- 按项目血缘去重并执行 T1—T4 严格筛选后，共现与五模式是否仍稳定？

## 精读补充（PaperForge 视角）

> [!note] 关于这一节
> 这一节在原报告的解释性阅读之上，补充作者思路重建、承重假设、最小证伪实验、强反例和后续方向。凡是论文没有直接声称的内容，正文都会说明它是重建、质疑或研究提议；这不是审稿评分，也不改变 `human_confirmed: false`。

### 作者是怎么走到“五维设计空间”的

ReAct 把 reasoning 与 action 交错成循环（arXiv:2210.03629）；Generative Agents 把长期记录、reflection 与 retrieval 做成可运行的记忆架构（arXiv:2304.03442）；Toolformer 说明模型能够学习何时调用外部 API（arXiv:2302.04761）；ChatDev 把多角色协作引入软件开发（arXiv:2307.07924）；SWE-agent 又显示 agent-computer interface 会直接改变 coding agent 的行为和成绩（arXiv:2405.15793）。这些工作逐项制造了 loop、context、tool、delegation 和 execution boundary 的工程压力，却没有解释这些压力在真实项目中怎样成套出现。

软件架构研究提供了另一半方法：Jansen 与 Bosch 把架构看作一组显式 design decisions（DOI:10.1109/WICSA.2005.61），Tofan 等人的系统映射说明 architectural-decision knowledge 可以跨项目积累（DOI:10.1016/j.infsof.2014.03.009）。把两条线接起来，研究问题就从“每个 framework 有哪些功能”变成“公开实现反复作出哪些架构决策，它们怎样共同出现”。论文没有声称这是作者真实的灵感过程；这是依据第 2 节和已核验前作作出的逆向重建。

### 整篇真正押在哪一条假设上

最承重的假设是：项目级编码矩阵足够准确、可比，而且 70 行可以近似当作 70 个独立的架构观测。第 3.4 节说每个项目按 14 模块调查，保留字段值、证据路径、置信说明和 coverage statement；15 项目的二次审计得到 94% 初始字段级一致率。这支持“编码经过结构化流程”，却不足以让外部读者复算：完整 extraction records、编码矩阵和横向综合都只是 internal audit materials，94% 也不是全矩阵或机会校正后的 κ/α。

样本独立性同样关键。附录 A 包含多个相关 `claw-*` 变体，论文没有报告 fork/项目血缘去重或 cluster-weighted sensitivity。若同一祖先设计被重复计数，五维比例和成束现象会同时被放大。这条假设失效时，边际分布、共现与五模式都会失去经验基础；论文公开材料目前更适合审查研究框架，尚不足以独立复现全部数字。

### 花一周就能把这条假设证伪的实验

从五种模式各取两个项目，再加入 `Pipeline/Stage` 与 `Context Window` 边界案例，共 12 个。两名没看过原标签的编码者只使用附录 B codebook、冻结 commit 和统一取证模板，独立记录五维类别、源码定位与 coverage statement，并额外按 arXiv:2606.10106 的 T1—T4 做成员测试。最后报告逐字段原始一致率与 κ/α，公开分歧样例，再从 12 行重算边际比例、support、confidence 和 lift。

若主要类别 κ 至少 0.8、第三人能复查证据定位、重算指标与表格定义一致，测量层获得支持。若多个维度 κ 偏低、严格成员测试排除大量样本，或核心共现无法由公开证据重算，论文最承重的经验层就被反驳。这个实验不必重做 70 项目普查，却直接检验分类的可操作性与数字的一致性。

### 如果要反驳，最强的反例长什么样

对原语料同时做“严格成员筛选”和“项目血缘去重”。2606.10106 的 T1 要求自适应 reasoning–action–observation 内循环，固定 pipeline 会被排除；其 T3 不接受机械 buffer 截断，T4 还要求独立于模型服从的控制。因此表 4 中唯一的 `Pipeline/Stage` 项目、表 5 的 `Context Window` 案例以及只有薄弱控制的项目，都需要重新核实成员资格。

随后把同一上游或生态的 claw 变体聚类，只保留一个代表或采用 cluster-weighted 统计。如果筛选与去重后表 4—9 的比例明显移动、表 10—12 的共现消失、表 14 的模式不稳定，“设计决策自然成束”就会面对一个更简单的替代解释：宽松纳入与相关样本制造了成束现象。即便反例成立，五维仍可作为阅读框架；被削弱的是“70 项目经验规律”的强度。

### 顺着缺口，一个值得做的新方向

可以把静态项目普查改造成 **Executable Harness Architecture Lab**：先用 T1—T4 建立成员门槛，再把 context strategy、tool boundary、delegation topology、isolation 和 audit 当作可替换 treatments，在同一 agent core、任务集合和预算下做多因素实验。第一轮固定模型与 ReAct loop，只做 2×2×2：session/file context、internal registry/MCP、host/container execution；每格运行多随机种子的软件维护任务，同时注入工具失败和 prompt injection，测成功率、恢复能力、上下文成本、越权行为和审计完备性。

OAgents 已对 agent components 做效果实验（arXiv:2506.15741），开发者实践研究已从 11,910 条讨论比较十个框架（arXiv:2512.01939），2606.10106 则提供成员测试。这个方向新增的是把严格成员定义、可替换运行时架构与多目标因果实验合成公开试验台。基于本次检索，没有在上述近邻中看到这一组合；这仍是检索后的研究提议，不是已经证明的全球首创。

## User notes
