#!/usr/bin/env python3
"""PaperWiki v1 CLI: discover, acquire, and deposit papers using stdlib only."""

import argparse, concurrent.futures, datetime as dt, hashlib, html, json, math, re, subprocess, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

UA = "PaperWiki/0.1 (+https://github.com/zss1033741393-tech/PaperWiki)"
WEIGHTS = {"relevance":.30,"venue":.20,"citations":.15,"recency":.15,"reproducibility":.10,"author_continuity":.05,"novelty":.05}
TOP_VENUES=("neurips","icml","iclr","acl","emnlp","cvpr","iccv","eccv","aaai","nature","science","jmlr")

def fetch(url, binary=False):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json, application/atom+xml;q=.9, */*;q=.8"})
    with urllib.request.urlopen(req,timeout=30) as r: data=r.read()
    return data if binary else data.decode("utf-8")

def norm_arxiv(value):
    m=re.search(r"(?:abs/|pdf/|arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?",value,re.I)
    return m.group(1) if m else None

def paper_id(p):
    if p.get("doi"): return "doi:"+p["doi"].lower().removeprefix("https://doi.org/")
    if p.get("arxiv_id"): return "arxiv:"+re.sub(r"v\d+$","",p["arxiv_id"],flags=re.I)
    title=re.sub(r"\W+"," ",p["title"].lower()).strip()
    return "title:"+hashlib.sha256(title.encode()).hexdigest()[:16]

def arxiv_search(query,limit):
    search='all:"'+query.replace('"','')+'"' if query else "all:*"
    url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode({"search_query":search,"start":0,"max_results":limit,"sortBy":"relevance","sortOrder":"descending"})
    root=ET.fromstring(fetch(url)); ns={"a":"http://www.w3.org/2005/Atom"}; out=[]
    for e in root.findall("a:entry",ns):
        aid=norm_arxiv(e.findtext("a:id",default="",namespaces=ns)); links={x.get("type"):x.get("href") for x in e.findall("a:link",ns)}
        out.append({"title":" ".join(e.findtext("a:title",default="",namespaces=ns).split()),"authors":[a.findtext("a:name",default="",namespaces=ns) for a in e.findall("a:author",ns)],"abstract":" ".join(e.findtext("a:summary",default="",namespaces=ns).split()),"year":int(e.findtext("a:published",namespaces=ns)[:4]),"arxiv_id":aid,"source_url":f"https://arxiv.org/abs/{aid}","pdf_url":links.get("application/pdf",f"https://arxiv.org/pdf/{aid}"),"provenance":[{"provider":"arxiv","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]})
    return out

def semantic_search(query,limit):
    fields="title,authors,year,venue,externalIds,url,abstract,citationCount,influentialCitationCount,openAccessPdf"
    url="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode({"query":query,"limit":limit,"fields":fields})
    out=[]
    for x in json.loads(fetch(url)).get("data",[]):
        ext=x.get("externalIds") or {}; oa=x.get("openAccessPdf") or {}
        out.append({"title":x.get("title") or "","authors":[a["name"] for a in x.get("authors",[])],"abstract":x.get("abstract"),"year":x.get("year"),"venue":x.get("venue") or None,"doi":ext.get("DOI"),"arxiv_id":ext.get("ArXiv"),"source_url":x.get("url"),"pdf_url":oa.get("url"),"citation_count":x.get("citationCount"),"influential_citation_count":x.get("influentialCitationCount"),"provenance":[{"provider":"semantic-scholar","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]})
    return out

def crossref_search(query,limit):
    url="https://api.crossref.org/works?"+urllib.parse.urlencode({"query":query,"rows":limit,"select":"DOI,title,author,published,container-title,URL,is-referenced-by-count,abstract"})
    out=[]
    for x in json.loads(fetch(url)).get("message",{}).get("items",[]):
        parts=(x.get("published") or {}).get("date-parts") or [[]]; year=parts[0][0] if parts and parts[0] else None
        out.append({"title":next(iter(x.get("title") or []),""),"authors":[" ".join(filter(None,[a.get("given"),a.get("family")])) for a in x.get("author",[])],"abstract":re.sub(r"<[^>]+>"," ",x.get("abstract") or ""),"year":year,"venue":next(iter(x.get("container-title") or []),None),"doi":x.get("DOI"),"source_url":x.get("URL"),"citation_count":x.get("is-referenced-by-count"),"provenance":[{"provider":"crossref","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]})
    return out

def openalex_search(query,limit):
    url="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":query,"per-page":limit,"select":"id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access,ids,abstract_inverted_index,relevance_score"})
    out=[]
    for x in json.loads(fetch(url)).get("results",[]):
        ids=x.get("ids") or {}; location=x.get("primary_location") or {}; source=location.get("source") or {}; inv=x.get("abstract_inverted_index") or {}; words=sorted(((pos,w) for w,poses in inv.items() for pos in poses),key=lambda z:z[0]); abstract=" ".join(w for _,w in words)
        arxiv=norm_arxiv(ids.get("arxiv") or ""); doi=(x.get("doi") or "").removeprefix("https://doi.org/") or None
        out.append({"title":x.get("title") or "","authors":[(a.get("author") or {}).get("display_name","") for a in x.get("authorships",[])],"abstract":abstract,"year":x.get("publication_year"),"venue":source.get("display_name"),"doi":doi,"arxiv_id":arxiv,"source_url":x.get("doi") or x.get("id"),"pdf_url":location.get("pdf_url"),"citation_count":x.get("cited_by_count"),"open_access":x.get("open_access"),"provider_relevance":x.get("relevance_score"),"provenance":[{"provider":"openalex","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]})
    return out

def huggingface_search(query,limit):
    """Discovery via Hugging Face Papers search: curated, arXiv-linked papers with community upvotes."""
    data=json.loads(fetch("https://huggingface.co/api/papers/search?"+urllib.parse.urlencode({"q":query}))); out=[]
    for item in data[:limit]:
        p=item.get("paper") or item; aid=p.get("id"); pub=p.get("publishedAt") or ""
        out.append({"title":p.get("title") or item.get("title") or "","authors":[a.get("name","") for a in p.get("authors",[])],"abstract":p.get("summary"),"year":int(pub[:4]) if pub[:4].isdigit() else None,"arxiv_id":aid,"source_url":f"https://huggingface.co/papers/{aid}","pdf_url":f"https://arxiv.org/pdf/{aid}" if aid else None,"hf_upvotes":p.get("upvotes",0),"hf_url":f"https://huggingface.co/papers/{aid}","hf_ai_summary":p.get("ai_summary"),"provenance":[{"provider":"huggingface-search","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]})
    return out

def huggingface_enrich(records):
    """Add Daily Papers engagement and linked-code evidence by arXiv ID."""
    def one(p):
        aid=p.get("arxiv_id")
        if not aid: return None
        try:
            x=json.loads(fetch("https://huggingface.co/api/papers/"+urllib.parse.quote(re.sub(r"v\d+$","",aid))))
            p["hf_upvotes"]=x.get("upvotes",0); p["hf_url"]="https://huggingface.co/papers/"+aid; p["github_url"]=x.get("githubRepo") or p.get("github_url"); p["project_url"]=x.get("projectPage") or p.get("project_url"); p["hf_ai_summary"]=x.get("ai_summary")
            p.setdefault("provenance",[]).append({"provider":"huggingface-papers","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()})
            return None
        except urllib.error.HTTPError as e:
            return None if e.code==404 else {"provider":"huggingface-papers","paper_id":aid,"error":str(e),"recoverable":True}
        except Exception as e: return {"provider":"huggingface-papers","paper_id":aid,"error":str(e),"recoverable":True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(one,records))
    return [x for x in results if x]

# Legal paper-search-mcp platforms usable as broader / open-access discovery providers.
# Sci-Hub ("sci_hub") is deliberately excluded: it is a copyright-circumvention source and is never queried.
LEGAL_PSM_PLATFORMS=("dblp","openalex","crossref","unpaywall","core","openaire","europepmc","doaj","zenodo")

def _psm_searchers():
    """Instantiate available paper-search-mcp legal searchers; return {} if the package is absent (stdlib-only env)."""
    import importlib,inspect; out={}
    for name in LEGAL_PSM_PLATFORMS:
        try:
            mod=importlib.import_module(f"paper_search_mcp.academic_platforms.{name}")
            cls=next((c for _,c in inspect.getmembers(mod,inspect.isclass) if c.__module__==mod.__name__ and hasattr(c,"search")),None)
            if cls: out[name]=cls()
        except Exception: pass
    return out

def _psm_to_record(p,name):
    extra=getattr(p,"extra",None) or {}; yr=str(extra.get("year") or ""); pub=getattr(p,"published_date",None)
    year=int(yr) if yr.isdigit() else (pub.year if pub else None)
    return {"title":getattr(p,"title","") or "","authors":list(getattr(p,"authors",None) or []),"abstract":getattr(p,"abstract",None) or None,"year":year,"doi":getattr(p,"doi",None) or None,"venue":extra.get("venue") or None,"pdf_url":getattr(p,"pdf_url",None) or None,"source_url":getattr(p,"url",None),"provenance":[{"provider":"psm-"+name,"retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}

def broader_search(query,limit,searchers=None):
    """Optional broader / open-access providers via paper-search-mcp (if installed). Per-source failure is tolerated. Sci-Hub is never used."""
    if searchers is None: searchers=_psm_searchers()
    out=[]
    for name,s in searchers.items():
        try: out+=[_psm_to_record(p,name) for p in s.search(query,limit)]
        except Exception: pass
    return out

def merge(records):
    seen={}; aliases={}
    for p in records:
        keys=[]
        if p.get("doi"): keys.append("doi:"+p["doi"].lower().removeprefix("https://doi.org/"))
        if p.get("arxiv_id"): keys.append("arxiv:"+re.sub(r"v\d+$","",p["arxiv_id"],flags=re.I))
        keys.append("title:"+hashlib.sha256(re.sub(r"\W+"," ",p["title"].lower()).strip().encode()).hexdigest()[:16])
        canonical=next((aliases[k] for k in keys if k in aliases),None); old=seen.get(canonical) if canonical else None
        if old:
            old["provenance"]+=p.get("provenance",[])
            for k,v in p.items():
                if v not in (None,"",[]) and old.get(k) in (None,"",[]): old[k]=v
            preferred=paper_id(old); old["paper_id"]=preferred
            if preferred!=canonical: seen[preferred]=seen.pop(canonical); canonical=preferred
        else:
            canonical=paper_id(p); p["paper_id"]=canonical; seen[canonical]=p
        for k in keys: aliases[k]=canonical
    return list(seen.values())

def score(p,query):
    title=(p.get("title") or "").lower(); abstract=(p.get("abstract") or "").lower(); text=title+" "+abstract; terms=list(dict.fromkeys(re.findall(r"\w+",query.lower())))
    title_overlap=sum(t in title for t in terms)/max(1,len(terms)); abstract_overlap=sum(t in abstract for t in terms)/max(1,len(terms)); phrase=query.lower() in title
    rel=min(1,.55*title_overlap+.35*abstract_overlap+.10*phrase); age=max(0,dt.date.today().year-(p.get("year") or 0)); rec=max(0,1-age/4)
    cites=p.get("citation_count"); venue=(p.get("venue") or "").lower(); code=bool(p.get("github_url") or re.search(r"github\.com|code (?:is|at|available)|paperswithcode",text)); data=bool(re.search(r"dataset (?:is|at|available)|data (?:is|at|available)",text)); upvotes=p.get("hf_upvotes")
    signals={"relevance":rel,"venue":.95 if any(v in venue for v in TOP_VENUES) else (.65 if venue else None),"citations":min(1,math.log1p(cites)/math.log(1001)) if cites is not None else None,"recency":rec,"reproducibility":min(1,.7*code+.3*data) if code or data else None,"author_continuity":None,"novelty":min(1,math.log1p(upvotes)/math.log(101)) if upvotes is not None else None}
    available={k:v for k,v in signals.items() if v is not None}; coverage=sum(WEIGHTS[k] for k in available); raw=sum(WEIGHTS[k]*v for k,v in available.items())/coverage; total=raw*(.5+.5*coverage)
    band="must-read" if total>=.8 and coverage>=.7 else "recommended" if total>=.65 else "candidate" if total>=.5 else "watch"
    flags=[]; low_title=(p.get("title") or "").lower()
    if "retracted" in low_title or "withdrawn" in low_title: flags.append("possible-retraction-or-withdrawal")
    evidence={"relevance":{"title_overlap":round(title_overlap,3),"abstract_overlap":round(abstract_overlap,3),"exact_title_phrase":phrase},"venue":p.get("venue"),"citations":cites,"recency":p.get("year"),"reproducibility":{"github":p.get("github_url"),"data_mentioned":data} if code or data else None,"author_continuity":None,"novelty":{"source":"Hugging Face Daily Papers upvotes","upvotes":upvotes,"url":p.get("hf_url")} if upvotes is not None else None}
    p.update({"status":"discovered","quality_flags":flags,"discovery":{"signals":signals,"signal_evidence":evidence,"missing_evidence":[k for k,v in signals.items() if v is None],"raw_score":round(raw,4),"score":round(total,4),"coverage":round(coverage,4),"band":band,"reasons":[f"topic relevance {rel:.0%}",f"published {p.get('year') or 'unknown'}",f"evidence coverage {coverage:.0%}","final score is confidence-adjusted by evidence coverage"]}}); return p

def cmd_discover(a):
    records=[]; errors=[]
    providers=[("arxiv",arxiv_search),("semantic-scholar",semantic_search),("crossref",crossref_search),("openalex",openalex_search)]
    if not a.no_huggingface: providers.append(("huggingface",huggingface_search))
    if getattr(a,"broader",False): providers.append(("broader",broader_search))
    for name,fn in providers:
        try: records+=fn(a.query,min(50,max(a.limit*5,a.limit)))
        except Exception as e: errors.append({"provider":name,"error":str(e),"recoverable":True})
    if not records: raise RuntimeError(json.dumps(errors,ensure_ascii=False))
    cutoff=dt.date.today().year-a.since_years+1 if a.since_years else None
    normalized=[p for p in merge(records) if not cutoff or not p.get("year") or p["year"]>=cutoff]
    if not a.no_huggingface: errors+=huggingface_enrich(normalized[:min(len(normalized),max(20,a.limit*3))])
    result=sorted((score(p,a.query) for p in normalized),key=lambda x:x["discovery"]["score"],reverse=True)[:a.limit]
    payload={"query":a.query,"papers":result,"errors":errors}; Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); print(a.output)

def resolve_arxiv(value):
    aid=norm_arxiv(value)
    if not aid: raise ValueError("Only arXiv IDs/URLs are supported by the dependency-free resolver")
    rows=arxiv_search(f"id:{aid}",1)
    if not rows: # API id query fallback
        root=ET.fromstring(fetch("https://export.arxiv.org/api/query?id_list="+aid));
        raise RuntimeError("arXiv metadata unavailable")
    return rows[0]

def cmd_read(a):
    aid=norm_arxiv(a.paper); local=Path(a.paper); doi=None; pdf_bytes=None
    doi_match=re.search(r"(?:doi\.org/)?(10\.\d{4,9}/\S+)",a.paper,re.I)
    if aid:
        root=ET.fromstring(fetch(f"https://export.arxiv.org/api/query?id_list={aid}")); ns={"a":"http://www.w3.org/2005/Atom"}; e=root.find("a:entry",ns)
        if e is None: raise RuntimeError("Paper not found")
        p={"title":" ".join(e.findtext("a:title",default="",namespaces=ns).split()),"authors":[x.findtext("a:name",default="",namespaces=ns) for x in e.findall("a:author",ns)],"abstract":" ".join(e.findtext("a:summary",default="",namespaces=ns).split()),"year":int(e.findtext("a:published",namespaces=ns)[:4]),"arxiv_id":aid,"source_url":f"https://arxiv.org/abs/{aid}","provenance":[{"provider":"arxiv","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}
        pdf_bytes=fetch(f"https://arxiv.org/pdf/{aid}",binary=True)
    elif local.is_file():
        p={"title":local.stem,"authors":[],"source_url":None,"provenance":[{"provider":"local-pdf","path":str(local.resolve()),"retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}; pdf_bytes=local.read_bytes()
    elif doi_match:
        doi=doi_match.group(1).rstrip(".,;)"); x=json.loads(fetch("https://api.crossref.org/works/"+urllib.parse.quote(doi,safe=""))).get("message",{}); parts=(x.get("published") or {}).get("date-parts") or [[]]
        p={"title":next(iter(x.get("title") or []),doi),"authors":[" ".join(filter(None,[v.get("given"),v.get("family")])) for v in x.get("author",[])],"abstract":re.sub(r"<[^>]+>"," ",x.get("abstract") or ""),"year":parts[0][0] if parts and parts[0] else None,"venue":next(iter(x.get("container-title") or []),None),"doi":doi,"source_url":x.get("URL") or "https://doi.org/"+doi,"provenance":[{"provider":"crossref","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}
    elif a.paper.startswith(("http://","https://")) and ".pdf" in a.paper.lower():
        p={"title":Path(urllib.parse.urlparse(a.paper).path).stem,"authors":[],"source_url":a.paper,"provenance":[{"provider":"direct-pdf","retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}]}; pdf_bytes=fetch(a.paper,binary=True)
    else: raise ValueError("Provide an arXiv URL/ID, DOI, direct PDF URL, or local PDF")
    p["paper_id"]=paper_id(p); p["status"]="reading"
    raw=Path(a.root)/"raw/papers"; reports=Path(a.root)/"reports"; raw.mkdir(parents=True,exist_ok=True); reports.mkdir(parents=True,exist_ok=True)
    stem=slug(p["paper_id"]); pdf=raw/f"{stem}.pdf"
    if pdf_bytes: pdf.write_bytes(pdf_bytes); p["pdf_path"]=str(pdf)
    report=reports/f"{stem}.md"; report.write_text(f"---\npaper_id: {p['paper_id']}\nstatus: reading\nsource: {p.get('source_url') or str(local)}\n---\n\n# {p['title']}\n\n## Abstract\n\n{p.get('abstract') or 'Metadata source did not provide an abstract.'}\n\n## Paper Craft analysis\n\n> Run `$paper-analyzer` from `vendor/paper-craft-skills` against `{p.get('pdf_path') or p.get('source_url')}` and replace this block with the reviewed analysis.\n\n## User notes\n\n",encoding="utf-8"); p["reading"]={"report_path":str(report),"paper_craft_skill":"paper-analyzer","analysis_status":"pending-agent-review","full_text_available":bool(pdf_bytes)}; (report.with_suffix(".json")).write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding="utf-8"); print(report)

def bullets(values): return "\n".join(f"- {v}" for v in values) if values else "- Not established from the available paper."

def cmd_finalize(a):
    report=Path(a.report); side=report.with_suffix(".json")
    if not side.exists(): raise FileNotFoundError(f"Missing reading record: {side}")
    p=json.loads(side.read_text(encoding="utf-8")); analysis=json.loads(Path(a.analysis).read_text(encoding="utf-8"))
    required=["research_question","contributions","method","experiments","findings","limitations","reproducibility","concepts","methods","datasets","topics","open_questions"]
    missing=[k for k in required if k not in analysis]
    if missing: raise ValueError("Analysis is missing fields: "+", ".join(missing))
    src=p.get("source_url") or p.get("pdf_path"); mermaid=analysis.get("mermaid") or "flowchart LR\n  A[Input] --> B[Method] --> C[Output]"; content=f'''---
paper_id: {p['paper_id']}
status: reviewed
source: {src}
generated: true
human_confirmed: false
---

# {p['title']}

> [!summary] 一句话结论
> {analysis.get('tldr','')}

## 论文信息

- 作者：{', '.join(p.get('authors') or [])}
- 年份：{p.get('year') or 'unknown'}
- Venue：{p.get('venue') or 'unknown'}
- 原文：{src}

## 研究问题

{analysis['research_question']}

## 核心贡献

{bullets(analysis['contributions'])}

## 方法直观解释

{analysis['method']}

```mermaid
{mermaid}
```

## 实验与证据

{bullets(analysis['experiments'])}

## 主要发现

{bullets(analysis['findings'])}

## 局限与风险

{bullets(analysis['limitations'])}

## 复现条件

{bullets(analysis['reproducibility'])}

## 关键概念

{bullets(analysis['concepts'])}

## 开放问题

{bullets(analysis['open_questions'])}

## 证据定位

{bullets(analysis.get('evidence',[]))}

## User notes

'''
    report.write_text(content,encoding="utf-8"); p["status"]="reviewed"; p["reading"].update(analysis); p["reading"]["analysis_status"]="generated-awaiting-human-confirmation"; side.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding="utf-8")
    out=report.with_suffix(".html"); generator=Path(__file__).parent/"vendor/paper-craft-skills/skills/paper-analyzer/scripts/generate_html.py"
    if generator.exists():
        try: subprocess.run([sys.executable,str(generator),str(report),str(out)],check=True,capture_output=True,text=True)
        except subprocess.CalledProcessError: out.write_text("<!doctype html><meta charset=utf-8><title>"+html.escape(p["title"])+"</title><style>body{max-width:900px;margin:auto;padding:2rem;font:16px/1.7 system-ui;white-space:pre-wrap}</style><body>"+html.escape(content)+"</body>",encoding="utf-8")
    else: out.write_text("<!doctype html><meta charset=utf-8><title>"+html.escape(p["title"])+"</title><style>body{max-width:900px;margin:auto;padding:2rem;font:16px/1.7 system-ui;white-space:pre-wrap}</style><body>"+html.escape(content)+"</body>",encoding="utf-8")
    print(report)

def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:80] or hashlib.sha256(s.encode()).hexdigest()[:16]

def link_entity(root, collection, name, paper_title, paper_target):
    folder=root/"wiki"/collection; folder.mkdir(parents=True,exist_ok=True); target=folder/(slug(name)+".md")
    link=f"- [[../papers/{paper_target}|{paper_title}]]\n"; old=target.read_text(encoding="utf-8") if target.exists() else f"---\ntitle: \"{name.replace(chr(34),chr(39))}\"\ntype: {collection.rstrip('s')}\n---\n\n# {name}\n\n## Related papers\n\n"
    target.write_text(old if link in old else old+link,encoding="utf-8"); return f"[[../{collection}/{target.stem}|{name}]]"

def cmd_deposit(a):
    src=Path(a.input); text=src.read_text(encoding="utf-8"); side=src.with_suffix(".json"); p=json.loads(side.read_text(encoding="utf-8")) if side.exists() else {"title":re.search(r"^#\s+(.+)$",text,re.M).group(1),"provenance":[{"provider":"user-notes","path":str(src)}]}
    p["paper_id"]=p.get("paper_id") or paper_id(p); root=Path(a.root); papers=root/"wiki/papers"; papers.mkdir(parents=True,exist_ok=True)
    target=papers/(slug(p["paper_id"])+".md"); existing=target.read_text(encoding="utf-8") if target.exists() else ""; human=""
    m=re.search(r"## User notes\s*(.*?)(?=\n## |\Z)",existing,re.S)
    if m: human=m.group(1).strip()
    reading=p.get("reading") or {}; entities=[]
    for key,collection in [("concepts","concepts"),("methods","methods"),("datasets","datasets"),("topics","topics")]:
        for name in reading.get(key,[]) or []: entities.append(link_entity(root,collection,str(name),p["title"],target.stem))
    body=f"---\npaper_id: {p['paper_id']}\ntitle: \"{p['title'].replace(chr(34),chr(39))}\"\nstatus: deposited\n---\n\n# {p['title']}\n\n## Source report\n\n[[{src.stem}]]\n\n## Related knowledge\n\n"+("\n".join(f"- {x}" for x in entities) if entities else "- No structured entities confirmed yet.")+f"\n\n## Generated synthesis (draft)\n\n{text}\n\n## User notes\n\n{human}\n"
    target.write_text(body,encoding="utf-8"); (root/"index.md").parent.mkdir(parents=True,exist_ok=True); idx=root/"index.md"; line=f"- [[wiki/papers/{target.stem}|{p['title']}]]\n"; old=idx.read_text(encoding="utf-8") if idx.exists() else "# PaperWiki Index\n\n"; idx.write_text(old if line in old else old+line,encoding="utf-8")
    log=root/"log.md"; old=log.read_text(encoding="utf-8") if log.exists() else "# Operation Log\n\n"; log.write_text(old+f"- {dt.datetime.now(dt.timezone.utc).isoformat()} deposit {p['paper_id']}\n",encoding="utf-8"); print(target)

def cmd_recommend(a):
    root=Path(a.root); topics=[]; concepts=[]
    for path in (root/"wiki/topics").glob("*.md"): topics.append(path.stem.replace("-"," "))
    for path in (root/"wiki/concepts").glob("*.md"): concepts.append(path.stem.replace("-"," "))
    query=a.topic or (topics[0] if topics else None)
    if not query: raise ValueError("Provide --topic or deposit topic pages first")
    known=set((topics+concepts)); candidates=merge(arxiv_search(query,a.limit*2)+crossref_search(query,a.limit*2))
    candidates=[score(p,query) for p in candidates if slug(p["title"]) not in known][:a.limit]
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({"topic":query,"basis":{"known_topics":topics,"known_concepts":concepts},"recommendations":candidates},ensure_ascii=False,indent=2),encoding="utf-8"); print(out)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(required=True)
    d=sub.add_parser("discover"); d.add_argument("query"); d.add_argument("--limit",type=int,default=10); d.add_argument("--since-years",type=int,default=2,help="Recent-year window; use 0 to disable"); d.add_argument("--no-huggingface",action="store_true",help="Skip Hugging Face Papers engagement enrichment"); d.add_argument("--broader",action="store_true",help="Also query paper-search-mcp legal providers (DBLP, Unpaywall, CORE, ...) if installed"); d.add_argument("--output",default="reading-lists/latest.json"); d.set_defaults(func=cmd_discover)
    r=sub.add_parser("read"); r.add_argument("paper"); r.add_argument("--root",default="."); r.set_defaults(func=cmd_read)
    f=sub.add_parser("finalize"); f.add_argument("report"); f.add_argument("analysis"); f.set_defaults(func=cmd_finalize)
    k=sub.add_parser("deposit"); k.add_argument("input"); k.add_argument("--root",default="."); k.set_defaults(func=cmd_deposit)
    n=sub.add_parser("recommend"); n.add_argument("--topic"); n.add_argument("--limit",type=int,default=5); n.add_argument("--root",default="."); n.add_argument("--output",default="reading-lists/recommended-next.json"); n.set_defaults(func=cmd_recommend)
    a=ap.parse_args()
    try: a.func(a)
    except Exception as e:
        event={"at":dt.datetime.now(dt.timezone.utc).isoformat(),"command":getattr(a,"func",lambda:None).__name__,"error":str(e),"recoverable":True}
        error_root=Path(getattr(a,"root","."))/".paperwiki"; error_root.mkdir(parents=True,exist_ok=True)
        with (error_root/"errors.jsonl").open("a",encoding="utf-8") as f: f.write(json.dumps(event,ensure_ascii=False)+"\n")
        print(json.dumps(event,ensure_ascii=False),file=sys.stderr); raise SystemExit(1)

if __name__=="__main__": main()
