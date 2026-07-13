# PaperWiki 三层验证结论报告

- 日期：2026-07-13　分支：`worktree-validation+multi-agent-2026`
- 目标：用真实 2026 多智能体论文，端到端验证三大能力——**发现质量、精读品味、wiki 准确**
- 查询：`"LLM multi-agent collaboration"`、`"multi-agent orchestration"`
- 方法：L1 确定性 pytest（30 绿）· L2 证据 rubric（对真实样本逐条判定）· L3 独立 LLM 评审

## 执行摘要

| 能力 | 判定 | 一句话 |
| --- | --- | --- |
| ① 发现论文质量够不够高 | 🟡 **PARTIAL** | 可靠找到真实、相关、透明排序的 2026 论文、容错强；但相关性精确匹配主导，会挤掉高质量精选论文、放引用越位 |
| ② 精读产出有没有品味 | ⏳ **待 L3**（机械项全 ✅） | 忠实、证据锚点齐全、数字可核、结构完整、mermaid 贴合方法；忠实/洞见由独立评审判分（进行中）|
| ③ 沉淀 wiki 准不准确 | ✅ **PASS** | 双向链接 19/19、实体一致、幂等、台账、无静默覆盖全通过；唯一瑕疵 F2（中文实体名→哈希文件名）|

**顺带产出**：把 HuggingFace 从"纯富集"升级为一等发现源；集成 paper-search-mcp 9 个合法源（Sci-Hub 排除）；**发现并修复 1 个真实 bug（F1）**；确定性测试 9→30。

## 环境与方法

- **环境**：uv 管理的 Python 3.12.10（`.venv`），整合 paper-craft / paper-search-mcp 合法依赖。详见 [ENV.md](ENV.md)。
- **provider 可用性**（本机 IP，间歇性）：Crossref/OpenAlex/HuggingFace 稳定；arXiv/Semantic Scholar/DBLP 间歇 429/503。**多源容错是刚需且已生效**。
- **全文获取**：arXiv export API 被封时，改经**浏览器读 `arxiv.org/html/<id>`** 取全文深读（本机实测可行，无需传 PDF）。
- **深度分析引擎**：vendored `paper-craft/paper-analyzer`（零 API key）；深读产物由智能体按其工作流产出，`paperwiki.py` 负责脚手架 + schema 校验 + 渲染。

## L1 确定性引擎测试：30 绿

`python -m unittest discover -s tests` → **Ran 30 tests, OK**（基线 9 → 30）。覆盖：评分(8)、身份合并、discover 429 容错、finalize schema/渲染(4)、deposit 幂等+双向链接、recommend 去重(2)、错误落盘。

## 能力① 发现质量：🟡 PARTIAL

样本：各查询 12 篇真实 2026 论文（[fixtures/discovery](fixtures/discovery/)）。逐条见 [rubrics/discovery-quality.md](rubrics/discovery-quality.md)。

**硬通过**：D3 排序单调+band 自洽（脚本验证）、D4 容错召回（S2 等挂掉仍各 12 篇）、D5 证据透明（24/24 篇带 signals/coverage/reasons）、D1 高 band 论文均切题。

**三条排序缺陷**（详见 [FINDINGS.md](FINDINGS.md) O1/O2/O3）：
- **O1** 相关性精确匹配主导：查 "multi-agent orchestration"，11 篇标题精确匹配的 arXiv 论文（rel=1.0）挤掉 HF 高赞精选（Orchestra-o1 up=48、Paper Circle up=31）。
- **O2** 引用越位：泛综述《A Survey of LLMs》(rel=0.17, cite=1418) 排到更相关论文之上。
- **O3** must-read 对新论文不可达：24 篇无一进 must-read（缺 venue/引用→coverage 低→天花板 ~0.73）。

**结论**：核心可靠，缺陷都在**排序权重取舍**（非召回、非正确性）。用户已定：**只报告不改权重**——见"待决项"。

## 能力② 精读品味：⏳ 待 L3（机械项全通过）

样本：LEMON（arXiv 2605.14483）深读 [analysis](fixtures/reading/2605-14483.analysis.json) + golden 2604.03295 校准。逐条见 [rubrics/reading-taste.md](rubrics/reading-taste.md)。

**机械项全 ✅**：R2 无幻觉（数据集/方法均在原文）、R3 证据锚点（指向 §3.1/§3.4/Table1-2/Fig5/AppxA）、R5 完整（12 节实质填充、finalize 通过）、R6 mermaid 贴合方法、R7 结构合规（MD+HTML 生成、含真实数字 90.72）。

**判读项（R1 忠实、R4 洞见）**：由独立 Claude 子智能体对照全文对抗式评审——_结果待回填_。

## 能力③ wiki 准确：✅ PASS

样本：LEMON read→finalize→deposit 到隔离 vault（[fixtures/vault](fixtures/vault/)，19 实体）。逐条见 [rubrics/wiki-accuracy.md](rubrics/wiki-accuracy.md)。

全部机械验证通过：**W1 双向链接 19/19**、W2 实体一致、**W3 幂等（重跑仍 1 页、笔记保全）**、W4 台账、W5 无静默覆盖。唯一瑕疵 **F2**（中文实体名 → 哈希文件名；链接不断、文件名不可读）。

## 发现汇总

| 编号 | 严重度 | 一句话 | 状态 |
| --- | --- | --- | --- |
| F1 | 🟡 | recommend 去重失效（slug 连字符 vs 空格名永不相等）| **已修复** + 回归测试 |
| F2 | 🟡 | 非 ASCII 实体名 → SHA-256 哈希文件名（slug 仅保 ASCII）| 记录，交用户决定 |
| O1 | 🟡 | 相关性精确匹配主导，挤掉高质量精选论文 | 待决（用户选不改权重）|
| O2 | 🟡 | 引用数让离题论文越位 | 待决 |
| O3 | 🟡 | must-read 对前沿新论文不可达 | 待决 |
| E1 | 🟢 | provider 从本机 IP 间歇限流（容错已覆盖）| 环境约束 |

## 待决项（交用户）

1. **发现排序调权**（O1/O2/O3）：是否提高 novelty 权重 / 抑制低相关的 citation 越位 / 放宽 must-read 的 coverage 门槛。当前决定：不改。
2. **F2 中文文件名**：是否让 `slug` 用 `re.UNICODE` 保留中文（或拼音转写）。当前：未改。

## 复现

```bash
uv venv --python 3.12 && uv pip install -e vendor/paper-search-mcp pytest
git submodule update --init vendor/paper-craft-skills vendor/paper-search-mcp
.venv/bin/python -m unittest discover -s tests -v          # L1: 30 绿
.venv/bin/python validation/harvest.py                     # 冻结发现 fixture
.venv/bin/python paperwiki.py read https://arxiv.org/abs/2605.14483 --root validation/fixtures/vault
.venv/bin/python paperwiki.py finalize validation/fixtures/vault/reports/arxiv-2605-14483.md validation/fixtures/reading/2605-14483.analysis.json
.venv/bin/python paperwiki.py deposit validation/fixtures/vault/reports/arxiv-2605-14483.md --root validation/fixtures/vault
```

## 局限

- provider 间歇限流使 live harvest 结果随时间波动（fixture 已冻结当次真实结果）。
- 精读"品味"含主观判读；以独立子智能体 + golden 锚点 + 机械忠实核对三管缓解，但非绝对客观。
- 深读全文依赖 `arxiv.org/html` 存在该论文的 HTML 版；无 HTML 版时需兜底上传 PDF。
