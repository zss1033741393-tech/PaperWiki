# L2 Rubric — 精读品味（Reading Taste）

**问题**：`read` → 深度分析产出是否有品味——忠实原文、有洞见、结构完整、不杜撰？

**样本**：`validation/fixtures/reading/2605-14483.analysis.json`（LEMON 深读，经浏览器读 `arxiv.org/html/2605.14483` 全文产出）+ golden `examples/scaling-teams-or-scaling-time.analysis.json`（2604.03295，品味校准锚点）。

判定：✅通过 / 🟡部分 / ❌不通过 / ⏳待 L3。

| ID | 准则 | 类型 | 结果 | 证据 |
| --- | --- | --- | --- | --- |
| R1 | 忠实性：findings/experiments 可定位原文；数字不杜撰 | 判定 | ⏳ 待 L3 | 机械核对通过：90.72 / 84.32 / 48.53 / 2.0→2.25 / 7.4M→8.3M / 1.30K→1.15K 均出自 Table 1/2、Fig 5；最终由 L3 对照全文独立判分 |
| R2 | 无幻觉：concepts/methods/datasets 均出自原文 | 机械+判定 | ✅ | 6 数据集(GSM8K/MMLU/…)、方法(LEMON/GRPO/反事实编辑/SFT/节点缓存)均在原文命中 |
| R3 | 证据锚点：evidence 指向页/节/图并与结论对应 | 机械 | ✅ | `evidence[]` 5 条分别指向 §3.1(式1-4)/§3.4(式8-13)/Table1/Table2/Fig5/Appendix A |
| R4 | 洞见：tldr 有信息量、contributions/open_questions 非套话 | 判定 | ⏳ 待 L3 | tldr 抓住"把编排写成单一可执行规范 + 只对被编辑字段施加反事实信用"的双核心；open_questions 针对泛化/扩展/teacher 依赖 |
| R5 | 完整：12 必填节实质填充、无灌水占位 | 机械+判定 | ✅ | finalize schema 校验通过；各节非默认句 |
| R6 | 可视：mermaid 反映真实方法流（非默认 A→B→C） | 判定 | ✅ | mermaid 画出 task→policy→YAML→校验→图执行→奖励→GRPO+反事实编辑→段级信用→更新，与 §3 一致 |
| R7 | 结构合规：过 finalize schema，生成 MD+HTML | 机械 | ✅ | finalize 无 ValueError；report.md(status reviewed, 含 90.72) + .html 均生成 |

## 结论：机械项 ✅ 全通过；品味判读（R1 忠实、R4 洞见）→ L3 独立评审（task 7）

深读产物结构完整、证据锚点齐全、数字可核、可视化贴合方法；"品味"的主观维度（是否真忠实、是否有洞见）刻意交由 **L3 LLM-judge 独立打分**以避免"自产自评"的循环，并用 golden 2604.03295 校准。
