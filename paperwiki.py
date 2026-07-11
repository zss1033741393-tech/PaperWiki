#!/usr/bin/env python3
"""PaperWiki v1 CLI: discover, acquire, and deposit papers using stdlib only."""

import argparse, datetime as dt, hashlib, json, math, re, sys, urllib.parse, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

UA = "PaperWiki/0.1 (+https://github.com/zss1033741393-tech/PaperWiki)"
WEIGHTS = {"relevance":.30,"venue":.20,"citations":.15,"recency":.15,"reproducibility":.10,"author_continuity":.05,"novelty":.05}

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
    url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode({"search_query":search,"start":0,"max_results":limit,"sortBy":"submittedDate","sortOrder":"descending"})
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

def merge(records):
    seen={}
    for p in records:
        p["paper_id"]=paper_id(p); old=seen.get(p["paper_id"])
        if old:
            old["provenance"]+=p.get("provenance",[])
            for k,v in p.items():
                if v not in (None,"",[]) and old.get(k) in (None,"",[]): old[k]=v
        else: seen[p["paper_id"]]=p
    return list(seen.values())

def score(p,query):
    text=((p.get("title") or "")+" "+(p.get("abstract") or "")).lower(); terms=re.findall(r"\w+",query.lower())
    rel=sum(t in text for t in terms)/max(1,len(terms)); age=max(0,dt.date.today().year-(p.get("year") or 0)); rec=max(0,1-age/5)
    cites=p.get("citation_count"); signals={"relevance":rel,"recency":rec}
    if p.get("venue"): signals["venue"]=.7
    if cites is not None: signals["citations"]=min(1,math.log1p(cites)/math.log(1001))
    coverage=sum(WEIGHTS[k] for k in signals); total=sum(WEIGHTS[k]*v for k,v in signals.items())/coverage
    band="must-read" if total>=.8 and coverage>=.7 else "recommended" if total>=.65 else "candidate" if total>=.5 else "watch"
    p.update({"status":"discovered","discovery":{"signals":signals,"score":round(total,4),"coverage":round(coverage,4),"band":band,"reasons":[f"topic relevance {rel:.0%}",f"published {p.get('year') or 'unknown'}"]}}); return p

def cmd_discover(a):
    records=[]; errors=[]
    for name,fn in [("arxiv",arxiv_search),("semantic-scholar",semantic_search),("crossref",crossref_search)]:
        try: records+=fn(a.query,a.limit)
        except Exception as e: errors.append({"provider":name,"error":str(e),"recoverable":True})
    if not records: raise RuntimeError(json.dumps(errors,ensure_ascii=False))
    result=sorted((score(p,a.query) for p in merge(records)),key=lambda x:x["discovery"]["score"],reverse=True)[:a.limit]
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

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(required=True)
    d=sub.add_parser("discover"); d.add_argument("query"); d.add_argument("--limit",type=int,default=10); d.add_argument("--output",default="reading-lists/latest.json"); d.set_defaults(func=cmd_discover)
    r=sub.add_parser("read"); r.add_argument("paper"); r.add_argument("--root",default="."); r.set_defaults(func=cmd_read)
    k=sub.add_parser("deposit"); k.add_argument("input"); k.add_argument("--root",default="."); k.set_defaults(func=cmd_deposit)
    a=ap.parse_args()
    try: a.func(a)
    except Exception as e: print(json.dumps({"error":str(e),"recoverable":True},ensure_ascii=False),file=sys.stderr); raise SystemExit(1)

if __name__=="__main__": main()
