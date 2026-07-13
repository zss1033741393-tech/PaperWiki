# L2 Rubric — wiki 准确（Deposit Accuracy）

**问题**：`deposit` 沉淀的 wiki 是否准确——链接对称、实体一致、幂等、可导航、不静默覆盖？

**样本**：`validation/fixtures/wiki/`（将真实深读的 2026 论文 finalize 后 deposit 到隔离 vault 的产物）。

判定：✅通过 / 🟡部分 / ❌不通过。类型：`机械`=可代码断言，`判定`=需人工判读。

| ID | 准则 | 类型 | 判定方法 | 结果 | 证据 |
| --- | --- | --- | --- | --- | --- |
| W1 | 双向链接：paper ↔ concept/method/dataset/topic 互指 | 机械 | 论文页含实体链接，且各实体页含回指该论文的 `../papers/` 链接 | _待填_ | _待填_ |
| W2 | 实体一致：wiki 抽取的实体 = analysis 的 concepts/methods/datasets/topics | 机械 | 集合比对 | _待填_ | _待填_ |
| W3 | 幂等：重跑 deposit → 仍 1 页，`## User notes` 手写内容保全 | 机械 | 二次 deposit 后统计页数 + 校验笔记 | _待填_ | _待填_ |
| W4 | 台账：`index.md` 收录该论文，`log.md` 追加 deposit 事件 | 机械 | 断言两文件含对应条目 | _待填_ | _待填_ |
| W5 | 无静默覆盖：人工段落不被生成内容覆盖；冲突保留 | 机械+判定 | 修改后重跑，校验人工段落存活 | _待填_ | _待填_ |
| W6 | 可导航：wiki 页可追溯到 source report 与原文链接 | 机械 | 断言页内含 report 反链与 source | _待填_ | _待填_ |

**结论（待填）**：PASS / PARTIAL / FAIL + 一段话说明。
