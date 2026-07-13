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
- **判断**：这是"发现质量够不够高"的**取舍问题**，非明确 bug——留待 **L2 发现质量 rubric** 结合真实样本评判（是否漏掉了人会想读的高质量论文）。

## E1 🟢 provider 从本机 IP 间歇性限流

- arXiv export API、Semantic Scholar：常态 429。
- Crossref、DBLP：间歇 429/503。
- OpenAlex、HuggingFace：最稳定。
- **含义**：多源合并 + 单源失败可容错是**刚需**且已生效（实测两次不同源存活组合都返回了真实 2026 论文）。full-text 深读改走浏览器 `arxiv.org/html`。
