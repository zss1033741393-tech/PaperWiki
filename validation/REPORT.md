# PaperWiki 三层验证结论报告

- 日期：2026-07-13　分支：`worktree-validation+multi-agent-2026`
- 目标：用真实 2026 多智能体论文，端到端验证三大能力——**发现质量、精读品味、wiki 准确**
- 查询：`"LLM multi-agent collaboration"`、`"multi-agent orchestration"`
- 方法：L1 确定性 pytest（30 绿）· L2 证据 rubric（对真实样本逐条判定）· L3 独立 LLM 评审

## 执行摘要

| 能力 | 判定 | 一句话 |
| --- | --- | --- |
| ① 发现论文质量够不够高 | 🟡 **PARTIAL** | 可靠找到真实、相关、透明排序的 2026 论文、容错强；O2 引用越位**已修复**，但 O1 相关性精确匹配主导仍会挤掉高质量精选论文 |
| ② 精读产出有没有品味 | ✅ **PASS（强）** | 独立评审：洞见/完整/对标 golden 均 **5/5**、核心数字全 verbatim 正确；忠实 **4/5**（3 处外围疏漏被评审抓到并已修正）|
| ③ 沉淀 wiki 准不准确 | ✅ **PASS** | 双向链接 19/19、实体一致、幂等、台账、无静默覆盖全通过；唯一瑕疵 F2（中文实体名→哈希文件名）|

**顺带产出**：把 HuggingFace 从"纯富集"升级为一等发现源；集成 paper-search-mcp 9 个合法源（Sci-Hub 排除）；**修复 2 项（F1 recommend 去重、O2 引用越位）**、解决 F2（英文实体名约定）；确定性测试 9→31。

## 环境与方法

- **环境**：uv 管理的 Python 3.12.10（`.venv`），整合 paper-craft / paper-search-mcp 合法依赖。详见 [ENV.md](ENV.md)。
- **provider 可用性**（本机 IP，间歇性）：Crossref/OpenAlex/HuggingFace 稳定；arXiv/Semantic Scholar/DBLP 间歇 429/503。**多源容错是刚需且已生效**。
- **全文获取**：arXiv export API 被封时，改经**浏览器读 `arxiv.org/html/<id>`** 取全文深读（本机实测可行，无需传 PDF）。
- **深度分析引擎**：vendored `paper-craft/paper-analyzer`（零 API key）；深读产物由智能体按其工作流产出，`paperwiki.py` 负责脚手架 + schema 校验 + 渲染。

## L1 确定性引擎测试：30 绿

`python -m unittest discover -s tests` → **Ran 31 tests, OK**（基线 9 → 31）。覆盖：评分(8)、身份合并、discover 429 容错、finalize schema/渲染(4)、deposit 幂等+双向链接、recommend 去重(2)、错误落盘。

## 能力① 发现质量：🟡 PARTIAL

样本：各查询 12 篇真实 2026 论文（[fixtures/discovery](fixtures/discovery/)）。逐条见 [rubrics/discovery-quality.md](rubrics/discovery-quality.md)。

**硬通过**：D3 排序单调+band 自洽（脚本验证）、D4 容错召回（S2 等挂掉仍各 12 篇）、D5 证据透明（24/24 篇带 signals/coverage/reasons）、D1 高 band 论文均切题。

**三条排序缺陷**（详见 [FINDINGS.md](FINDINGS.md) O1/O2/O3）：
- **O1** 相关性精确匹配主导：查 "multi-agent orchestration"，11 篇标题精确匹配的 arXiv 论文（rel=1.0）挤掉 HF 高赞精选（Orchestra-o1 up=48、Paper Circle up=31）。
- **O2** 引用越位：泛综述《A Survey of LLMs》(rel=0.17, cite=1418) 排到更相关论文之上。
- **O3** must-read 对新论文不可达：24 篇无一进 must-read（缺 venue/引用→coverage 低→天花板 ~0.73）。

**结论**：核心可靠，缺陷都在**排序权重取舍**（非召回、非正确性）。用户已定：**只报告不改权重**——见"待决项"。

## 能力② 精读品味：✅ PASS（强）

样本：LEMON（arXiv 2605.14483）深读 [analysis](fixtures/reading/2605-14483.analysis.json) + golden 2604.03295 校准。逐条见 [rubrics/reading-taste.md](rubrics/reading-taste.md)。

**机械项全 ✅**：无幻觉、证据锚点（§3.1/§3.4/Table1-2/Fig5/AppxA）、完整、mermaid 贴合方法、结构合规。

**L3 独立评审**（全新上下文 Claude 子智能体，自行抓取全文核对，见 [judge/scores](judge/scores/2605-14483.json)）：
- 洞见 **5/5**、完整 **5/5**、对标 golden **5/5**——"精读产出有品味"得到独立佐证。
- 忠实 **4/5**：核心量化 claim（90.72、四 delta、消融、Fig5）**全部逐字正确**；扣分因 3 处**外围**疏漏——把 13 个基线误数成 14、误称"原文无局限章节"（实为 Appendix B）、称 worker 型号未指明（实为 Appendix D.2 Table 3 = Qwen2.5-7B/14B/32B）。**三处均已据评审修正**。

**结论**：深读产物洞见与完整度对标甚至超过 golden，核心事实零杜撰；3 处疏漏皆因漏读附录 B/D，被独立评审抓到并修正——**这条 `read → 独立 judge → 修正` 闭环本身佐证了系统能力**。

## 能力③ wiki 准确：✅ PASS

样本：LEMON read→finalize→deposit 到隔离 vault（[fixtures/vault](fixtures/vault/)，19 实体）。逐条见 [rubrics/wiki-accuracy.md](rubrics/wiki-accuracy.md)。

全部机械验证通过：**W1 双向链接 19/19**、W2 实体一致、**W3 幂等（重跑仍 1 页、笔记保全）**、W4 台账、W5 无静默覆盖。唯一瑕疵 **F2**（中文实体名 → 哈希文件名；链接不断、文件名不可读）。

## 发现汇总

| 编号 | 严重度 | 一句话 | 状态 |
| --- | --- | --- | --- |
| F1 | 🟡 | recommend 去重失效（slug 连字符 vs 空格名永不相等）| **已修复** + 回归测试 |
| O2 | 🟡 | 引用数让离题论文越位 | **已修复**（citation×relevance）+ 回归测试；综述 0.610→0.471 |
| F2 | 🟡 | 非 ASCII 实体名 → SHA-256 哈希文件名 | **已解决**（实体名用英文，与 golden 约定一致）|
| O1 | 🟡 | 相关性精确匹配主导，挤掉高质量精选论文 | 待决（用户选不改权重）|
| O3 | 🟡 | must-read 对前沿新论文不可达 | 待决 |
| E1 | 🟢 | provider 从本机 IP 间歇限流（容错已覆盖）| 环境约束 |

## 已处理 / 待决项

- **O2 引用越位**：✅ 已修复（`citation *= relevance`）+ 回归测试。
- **F2 实体名文件名**：✅ 已解决（实体名统一用英文，与 golden 约定一致）。
- **O1 相关性精确匹配主导** / **O3 must-read 对新论文不可达**：仍开放。用户已选**不改权重**；若日后要调，可提高 novelty 权重、放宽 must-read 的 coverage 门槛或增设"新星"档。

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
