#!/usr/bin/env python3
"""Render a PaperWiki Markdown report as a styled KaTeX/Mermaid HTML article."""

import argparse
import html
import re
from pathlib import Path

import markdown


def render(source: Path, output: Path) -> None:
    text = source.read_text(encoding="utf-8")
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1) if title_match else source.stem
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', body, flags=re.S)
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}]}})"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script><script>mermaid.initialize({{startOnLoad:true,theme:'neutral'}})</script>
<style>
:root{{--ink:#172033;--muted:#64748b;--accent:#2563eb;--line:#dbe4f0;--paper:#fff;--bg:#f4f7fb}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.85 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}}
article{{max-width:920px;margin:32px auto;padding:56px 72px;background:var(--paper);box-shadow:0 12px 40px #1e3a5f18;border-radius:18px}}
h1{{font-size:2.35rem;line-height:1.3;margin:0 0 2rem}} h2{{margin-top:3rem;padding-bottom:.5rem;border-bottom:1px solid var(--line);color:#174ea6}} h3{{margin-top:2rem}}
p{{margin:1rem 0}} blockquote{{margin:1.5rem 0;padding:1rem 1.25rem;background:#eff6ff;border-left:4px solid var(--accent);border-radius:0 10px 10px 0}}
table{{width:100%;border-collapse:collapse;margin:1.4rem 0;font-size:.93rem}} th,td{{padding:.7rem .8rem;border:1px solid var(--line);vertical-align:top}} th{{background:#f1f5f9}}
pre:not(.mermaid){{overflow:auto;padding:1rem 1.2rem;background:#0f172a;color:#e2e8f0;border-radius:10px}} code{{font-family:"SFMono-Regular",Consolas,monospace}}
.katex-display{{overflow-x:auto;overflow-y:hidden;padding:.5rem 0}} a{{color:var(--accent)}}
@media(max-width:760px){{article{{margin:0;padding:28px 20px;border-radius:0}}h1{{font-size:1.75rem}}body{{font-size:16px}}}}
</style></head><body><article>{body}</article></body></html>'''
    output.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.source, args.output)
