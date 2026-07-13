# L2 Rubric — 精读品味（Reading Taste）

**问题**：`read` → 深度分析产出是否有品味——忠实原文、有洞见、结构完整、不杜撰？

**样本**：`validation/fixtures/reading/*.analysis.json`（新深读的 2026 论文 + golden `2604.03295` 作校准锚点）。深读经浏览器读 `arxiv.org/html/<id>` 全文、走 paper-analyzer 工作流。

判定：✅通过 / 🟡部分 / ❌不通过。类型：`机械`=可代码断言，`判定`=需人工/LLM 对照原文判读。

| ID | 准则 | 类型 | 判定方法 | 结果 | 证据 |
| --- | --- | --- | --- | --- | --- |
| R1 | 忠实性：`findings`/`experiments` 每条可在原文定位；venue/数字不杜撰 | 判定 | 逐条对照 `arxiv.org/html` 全文；抽查数字 | _待填_ | _待填_ |
| R2 | 无幻觉：抽取的 `concepts`/`methods`/`datasets` 均出自原文 | 机械+判定 | 关键词在全文中检索命中 | _待填_ | _待填_ |
| R3 | 证据锚点：`evidence` 提供页/节/图定位，且与结论对应 | 机械+判定 | 断言 `evidence` 非空且指向具体位置 | _待填_ | _待填_ |
| R4 | 洞见：`tldr` 有信息量、`contributions`/`open_questions` 非套话 | 判定 | 人工 + L3 judge 品味打分 | _待填_ | _待填_ |
| R5 | 完整：schema 12 个必填节均实质填充，无灌水占位 | 机械+判定 | 断言字段存在且非空/非默认句 | _待填_ | _待填_ |
| R6 | 可视：`mermaid` 反映真实方法流（非默认 A→B→C 占位） | 判定 | 对照方法节读图 | _待填_ | _待填_ |
| R7 | 结构合规：通过 `finalize` schema 校验，生成 MD+HTML | 机械 | 运行 finalize 无 ValueError，产物存在 | _待填_ | _待填_ |

**结论（待填）**：PASS / PARTIAL / FAIL + 一段话说明。
