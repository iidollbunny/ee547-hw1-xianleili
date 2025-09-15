#!/usr/bin/env python3
import json, os, re, time
from datetime import datetime, timezone
from glob import glob
from html import unescape

def strip_html(html):
    html=re.sub(r"<script[^>]*>.*?</script>","",html,flags=re.S|re.I)
    html=re.sub(r"<style[^>]*>.*?</style>","",html,flags=re.S|re.I)
    links=re.findall(r'href=[\'"]?([^\'" >]+)',html,flags=re.I)
    images=re.findall(r'src=[\'"]?([^\'" >]+)',html,flags=re.I)
    text=re.sub(r"<[^>]+>"," ",html)
    text=unescape(text)
    text=re.sub(r"\s+"," ",text).strip()
    return text,links,images

def count_stats(text):
    words=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text.lower())
    sentences=re.split(r"[.!?]+",text)
    paras=[p for p in re.split(r"\n\s*\n",text) if p.strip()]
    wc=len(words); sc=len([s for s in sentences if s.strip()]); pc=max(len(paras),1)
    avg=(sum(len(w) for w in words)/wc) if wc else 0.0
    return {"word_count":wc,"sentence_count":sc,"paragraph_count":pc,"avg_word_length":round(avg,4)}

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Processor start",flush=True)
    while not os.path.exists("/shared/status/fetch_complete.json"):
        print("Waiting for fetch_complete.json ...",flush=True); time.sleep(2)

    os.makedirs("/shared/processed",exist_ok=True)
    os.makedirs("/shared/status",exist_ok=True)

    pages=sorted(glob("/shared/raw/*.html"))
    if not pages:
        with open("/shared/status/process_complete.json","w") as f:
            json.dump({"timestamp":datetime.now(timezone.utc).isoformat(),"files":[]},f,indent=2)
        print("No raw pages found. Processor done (0 files).",flush=True)
        return

    for p in pages:
        name=os.path.basename(p)
        with open(p,errors="ignore") as f: html=f.read()
        text,links,images=strip_html(html)
        stats=count_stats(text)
        out={"source_file":name,"text":text,"statistics":stats,"links":links,"images":images,
             "processed_at":datetime.now(timezone.utc).isoformat()}
        base=os.path.splitext(name)[0]
        with open(f"/shared/processed/{base}.json","w") as f: json.dump(out,f,indent=2)

    with open("/shared/status/process_complete.json","w") as f:
        json.dump({"timestamp":datetime.now(timezone.utc).isoformat(),"files":[os.path.basename(p) for p in pages]},f,indent=2)

    print(f"[{datetime.now(timezone.utc).isoformat()}] Processor done",flush=True)

if __name__=="__main__":
    main()
