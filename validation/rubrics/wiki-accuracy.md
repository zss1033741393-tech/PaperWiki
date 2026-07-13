# L2 Rubric — wiki 准确（Deposit Accuracy）

**问题**：`deposit` 沉淀的 wiki 是否准确——链接对称、实体一致、幂等、可导航、不静默覆盖？

**样本**：`validation/fixtures/vault/`（LEMON 论文 read→finalize→deposit 到隔离 vault 的真实产物；19 个实体：5 概念/5 方法/6 数据集/3 主题）。

判定：✅通过 / 🟡部分 / ❌不通过。

| ID | 准则 | 类型 | 结果 | 证据 |
| --- | --- | --- | --- | --- |
| W1 | 双向链接：paper ↔ concept/method/dataset/topic 互指 | 机械 | ✅ | 脚本验证 **19/19 实体页均含回指该论文的反链**；论文页含全部 19 个实体链接 |
| W2 | 实体一致：wiki 实体 = analysis 抽取实体 | 机械 | ✅ | 19 = analysis 的 5 concepts+5 methods+6 datasets+3 topics，一一对应 |
| W3 | 幂等：重跑 deposit → 仍 1 页，人工笔记保全 | 机械 | ✅ | 注入 `MY_VALIDATION_NOTE` 后重跑：paper 页 1→1，笔记保留，概念页数稳定(5) |
| W4 | 台账：`index.md` 收录、`log.md` 追加 deposit | 机械 | ✅ | 两文件均含 `arxiv-2605-14483` / deposit 条目 |
| W5 | 无静默覆盖：人工段落不被生成内容覆盖 | 机械 | ✅ | 重跑后 `## User notes` 手写内容存活（同 W3） |
| W6 | 可导航：wiki 页可追溯 source report 与原文 | 机械 | 🟡 | 论文页含 `[[report]]` 反链 + source URL（可追溯）；但 **F2**：中文实体页文件名为哈希，文件系统层导航差 |

## 结论：✅ PASS（含 F2 次要瑕疵）

链接对称性、实体一致性、幂等性、台账、无静默覆盖**全部机械验证通过**——这是三大能力里最扎实的一项。唯一瑕疵是 **F2**（中文实体名 → 哈希文件名）：Obsidian 链接不断、显示名正确，但文件系统层不可读。属可选修复的设计选择，不影响链接正确性。
