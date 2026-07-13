# L2 Rubric — 发现质量（Discovery Quality）

**问题**：`discover` 找到的论文质量是否够高？排序是否可信、噪声是否被压低、容错是否保住召回？

**样本**：`validation/fixtures/discovery/{llm-multi-agent-collaboration,multi-agent-orchestration}.json`（2026-07-13 真跑冻结，各 12 篇真实 2026 论文）。

判定：✅通过 / 🟡部分 / ❌不通过。类型：`机械`=可代码断言，`判定`=需人工/LLM 判读。

| ID | 准则 | 类型 | 结果 | 证据 |
| --- | --- | --- | --- | --- |
| D1 | 切题性：高 band 论文 relevance ≥ 0.5 且主题词命中标题 | 机械 | ✅ | q1 top-4(recommended) rel 0.90–1.00；q2 全部 rel=1.00；无高 band 低相关项 |
| D2 | 噪声抑制：泛综述/离题不进 must-read | 机械+判定 | 🟡 | 唯一离题项《A Survey of Large Language Models》(rel=0.17) 正确落 **candidate**，未进 recommended；但因 cite=1418 排到 #9(0.610)，**压过 #10–12 更相关论文(rel 0.73–0.81)** |
| D3 | 排序自洽：按 score 降序、band 与阈值一致 | 机械 | ✅ | 两 fixture 均 `monotonic=True band_consistent=True`（脚本硬验） |
| D4 | 容错召回：部分源 429/503 仍返回 ≥5 篇真实相关 | 机械 | ✅ | q1 仅 S2 失败→12 篇；q2 S2+HF富集失败→12 篇；均真实 2026 相关 |
| D5 | 证据透明：每篇含 signals/coverage/reasons/missing_evidence | 机械 | ✅ | 24/24 篇字段齐全（脚本硬验） |
| D6 | 值不值得读：top-5 是否真·有价值 | 判定 | 🟡 | q1 佳：含 up=51《Beyond Individual Intelligence》综述(#3)、AAAI 论文(#2)；q2 差：top-12 全是 arXiv 精确匹配，偏**细分应用**(RTL 生成/3D 场景/材料筛选/VC 尽调)，非该方向最核心论文 |
| D7 | 高质量漏检：高赞/公认重要论文是否被相关性权重过度压低 | 判定 | 🟡 | **确认(=O1)**：q2 中 11 篇标题精确含"multi-agent orchestration"的 arXiv 论文(rel=1.0)**完全挤掉** HF 精选高赞 2026 论文(Orchestra-o1 up=48、Paper Circle up=31)；novelty 权重 0.05 敌不过 relevance 0.30 |

## 结论：🟡 PARTIAL（核心可靠，排序有真实取舍缺陷）

**够高的部分**：可靠地找到**真实、相关、2026** 的论文；排序单调自洽、证据完全透明、多源容错强（两次不同源存活组合都稳定返回 12 篇）。这三点是硬通过。

**不够高的部分**（均为**排序**而非召回问题）：
1. **相关性精确匹配主导**（D7/O1）：标题精确含查询短语几乎决定排序，把社区公认的高质量精选论文（Orchestra-o1 等）挤出榜单——尤其查询越"像短语"越严重。
2. **引用可让离题论文越位**（D2/O2）：cite=1418 的泛 LLM 综述(rel=0.17)排到更相关论文之上。
3. **must-read 对新论文不可达**（O3）：置信度按 coverage 折算，新 2026 论文缺 venue/citation → coverage≤0.55 → 最高仅 ~0.73，**没有任何论文进 must-read**，band 体系对前沿论文坍缩为 recommended/candidate。

**建议**：这些是权重取舍，非正确性错误（相关性优先本身可辩护）。是否调权（如提高 novelty、对低相关论文抑制 citation 越位、放宽 must-read 的 coverage 门槛）应由用户决定——见 REPORT 待决项。
