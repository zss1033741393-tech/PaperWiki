# 验证发现记录（滚动累积）

编号规则：`F#` 缺陷 / `O#` 观察 / `E#` 环境约束。严重度：🔴高 🟡中 🟢低。

## F1 🟡 recommend 去重失效（已修复）

- **现象**：`recommend` 未能排除已存在于本地 wiki 的论文——标题与某概念/主题页同名的候选仍出现在推荐里。
- **根因**：`cmd_recommend` 中 `known` 存的是**空格化名**（`path.stem.replace("-"," ")` → `"agent memory"`），但过滤用 `slug(p["title"])` 得到**连字符串**（`"agent-memory"`），两者永不相等，去重恒为假。
- **影响**：违反 ACCEPTANCE"a scored reading list distinct from local page identities"；已读过、已沉淀的论文会被反复推荐。
- **修复**：`known={slug(name) for name in topics+concepts}`，两侧统一走 `slug()`。
- **证据**：[tests/test_recommend.py](../tests/test_recommend.py) `test_excludes_papers_matching_known_wiki_pages`（先 RED 复现，修复后 GREEN）。

## O1 🟡 发现排序被"相关性"主导，或压低高质量论文

- **现象**：对 `"multi-agent orchestration"`，HF 返回的 40 篇中 29 篇为 2026，含 Orchestra-o1（upvotes=48）、"Beyond Individual Intelligence" 综述（upvotes=51）等高关注论文；但最终 top-8 全是标题精确含查询词的 arXiv 论文，高赞 HF 论文落到 9 名开外。
- **根因**：`score()` 中 `relevance` 权重 0.30，而 `novelty`(HF upvotes) 仅 0.05；标题精确匹配（含 exact-phrase 加成）几乎决定排序。
- **已证实**（真实 fixture）：查询 `"multi-agent orchestration"` 的最终 top-12 全部是标题精确含该短语的 arXiv 论文（rel=1.0），**Orchestra-o1(up=48)、Paper Circle(up=31) 等 HF 精选高赞 2026 论文被完全挤出**。
- **判断**：权重取舍，非正确性 bug（相关性优先可辩护）。是否调权交用户决定（见 REPORT 待决项）。证据：[rubrics/discovery-quality.md](rubrics/discovery-quality.md) D7。

## O2 🟡 引用数可让离题论文越位

- **现象**：查询 `"LLM multi-agent collaboration"`，泛化综述《A Survey of Large Language Models》(relevance=0.17) 因 cite=1418 排到 #9(score 0.610)，**压过 #10–12 真正相关的多智能体论文(rel 0.73–0.81)**。
- **根因**：citations 权重 0.15 + 对数归一，高被引可抵消低相关。该综述正确未进 recommended（噪声抑制部分生效），但仍在 candidate 内越位。
- **判断**：取舍问题。可选缓解：低相关(rel<阈值)时抑制 citation 贡献。证据：discovery-quality.md D2。

## O3 🟡 must-read 档对前沿新论文实际不可达

- **现象**：两查询 24 篇 2026 论文**无一进 must-read**，最高仅 ~0.733。
- **根因**：`total = raw*(.5+.5*coverage)`，新论文缺 venue/citation → coverage≤0.55 → 天花板 ~0.73<0.8。must-read 还要求 coverage≥0.7，新论文更难达。
- **判断**：设计上"证据不足则不敢标 must-read"可辩护，但导致 band 体系对最前沿论文坍缩为 recommended/candidate。可选：放宽 must-read 的 coverage 门槛或增设"新星"档。证据：discovery-quality.md D6/结论。

## F2 🟡 非 ASCII 实体名 → 不可读哈希文件名

- **现象**：deposit 后中文概念/方法页文件名变哈希（`concepts/fb7f97147752e774.md` ← "组合式可执行编排"），本例 7/19 实体如此；英文实体（LEMON/GRPO/GSM8K/MMLU）正常。
- **根因**：`slug()=re.sub(r"[^a-z0-9]+","-",...)` 只保留 ASCII 字母数字；中文字符全被删→空串→回退 SHA-256 哈希前缀。
- **影响**：Obsidian 双向链接仍可用（显示名是中文、目标指向哈希文件，链接不断），但**文件系统层不可读、难导航**——对以中文沉淀的知识库尤其明显（本项目 finalize 模板本身是中文）。
- **可选修复**：`slug` 用 `re.UNICODE` 保留 unicode 词字符（中文文件名），或加拼音转写。属设计选择（是否要中文文件名），故记为发现交用户决定，未擅改。
- **证据**：`validation/fixtures/vault/wiki/concepts/` 下 5 个哈希文件；[wiki-accuracy.md](rubrics/wiki-accuracy.md) W1 脚注。

## E1 🟢 provider 从本机 IP 间歇性限流

- arXiv export API、Semantic Scholar：常态 429。
- Crossref、DBLP：间歇 429/503。
- OpenAlex、HuggingFace：最稳定。
- **含义**：多源合并 + 单源失败可容错是**刚需**且已生效（实测两次不同源存活组合都返回了真实 2026 论文）。full-text 深读改走浏览器 `arxiv.org/html`。
