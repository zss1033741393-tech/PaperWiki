# Complementary reading sections: PaperForge § mapping

`read-source` produces the primary explanatory report. `deepen-reading` adds only the reading angles that report usually skips — the ones PaperForge is distinctive for. The block appended to `report.md`:

```
## 精读补充（PaperForge 视角）

> [!note] 关于这一节
> 这一节用 PaperForge 的读法，接着补上第一遍精读没怎么展开的几个角度……它是"接着往深里读"，不是给论文打审稿分。凡是论文没有明说、属于我的推断或猜测的地方，文中都会直接讲明，不当成论文本身的结论。

### 作者是怎么走到 <核心 idea> 的        ← PaperForge §3（重建思路）
### 整篇真正押在哪一条假设上              ← PaperForge §9（最承重/最脆弱的假设）
### 花一周就能把这条假设证伪的实验         ← PaperForge §10（最小验证实验）
### 如果要反驳，最强的反例长什么样         ← PaperForge §11（最强反例）
### 顺着缺口，一个值得做的新方向           ← PaperForge §12（非增量 follow-up）
```

Use natural, descriptive Chinese headings (like above) rather than "R1/R2" or "审稿" labels. The section is a reading complement, so the framing and voice are "接着读", not "评审".

## Why these five and not all twelve

| PaperForge § | Covered by read-source's report? | In this supplement |
|---|---|---|
| §1 problem / §2 prior work | yes | no |
| §4 intuition / §5 pipeline / §6 math | yes | no |
| §7 experiments / §8 takeaways | yes | no |
| §3 reconstruct reasoning | rarely | **yes** — how the idea plausibly formed |
| §9 load-bearing assumption | report lists many limitations | **yes** — crown the single most damaging one |
| §10 minimum experiment | no | **yes** |
| §11 counter-case | no | **yes** |
| §12 follow-up idea | report lists open questions | **yes** — one concrete, buildable, non-incremental direction |

The value is depth the first pass lacked: §3 is pure reading insight (how a serious researcher gets from prior knowledge to this idea, without using the paper's conclusion as a premise); §9 picks the *one* assumption whose failure is most damaging instead of enumerating; §12 commits to *one* buildable direction with (a) the gap it answers, (b) the neighboring field it borrows from, (c) the first experiment.

## Content per section

- **作者是怎么走到 idea 的** — Use only knowledge that predates the paper (prior background, known failure modes, empirical observations, related work). Simulate the path to the idea; do not use the paper's own contribution as a premise. Close by naming it as a reconstruction, not the authors' own account.
- **整篇押在哪条假设上** — One assumption. State it, say precisely why it may not hold, and what evidence the paper gives for it or is missing.
- **花一周证伪的实验** — What data, what to build, what to measure, which result supports vs. refutes. Prefer something runnable in ~a week without reproducing the full system.
- **最强的反例** — The strongest attack: an experiment, argument, or real scenario that genuinely challenges the claim. A good one either offers an alternative explanation for the paper's results or names conditions where the method predictably fails.
- **值得做的新方向** — Non-incremental. Not "apply to domain X" or "add a module for case Y". A new framing/objective/connection, with (a)/(b)/(c) and a clear boundary against existing work.

## Survey / position / benchmark adaptation

Reframe, do not skip:

- **assumption** — the most vulnerable *organizing* assumption (taxonomy completeness/exclusivity, or whether the central recommendation generalizes).
- **experiment** — a one-week study testing whether the framework earns its claim: e.g. can independent coders apply the taxonomy with high agreement (inter-coder κ), or does it actually predict the design choices it says it explains?
- **counter-case** — a real system or paper the framework misclassifies, or a domain where its headline recommendation predictably fails.
- **follow-up** — turn the static synthesis into something testable or living (e.g. a machine-readable, evidence-graded, continuously-updated version), framed as new work, not a wish already in the report's open questions.

## Voice and rendering (both matter)

- Natural prose, PaperForge style (Karpathy / Kaiming He as transferable technical-writing anchors): concrete first, claim before evidence, plain words, visible uncertainty, no low-information filler. **No 【推断】/【猜测】prefix tags** — carry source honesty in the wording.
- **Obsidian-safe math:** the vault is read in Obsidian, whose inline-math parser is stricter than the HTML's KaTeX. Avoid inline `$...$` inside list items and any `$...$` with a bare `*` (e.g. `J^*`) — it leaks as raw source and stray `*` become italics. Prefer plain Unicode (ΔJ, ε, κ, π) and reference existing formulas by location; reserve LaTeX for standalone `$$...$$` display blocks. Confirm with `verify_report.py` (HTML) and a browser/Obsidian spot-check.
