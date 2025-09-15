#!/usr/bin/env python3
import json, os, sys, time, urllib.request
from datetime import datetime, timezone

def fetch_once(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (EE547-HW1)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Fetcher start", flush=True)
    input_file = "/shared/input/urls.txt"
    while not os.path.exists(input_file):
        print(f"Waiting for {input_file}...", flush=True)
        time.sleep(2)

    with open(input_file) as f:
        urls=[line.strip() for line in f if line.strip()]

    os.makedirs("/shared/raw",exist_ok=True)
    os.makedirs("/shared/status",exist_ok=True)

    results=[]
    for i,url in enumerate(urls,1):
        out=f"/shared/raw/page_{i}.html"
        ok=False; err=None
        for attempt in range(3):
            try:
                print(f"Fetching {url} try {attempt+1}/3",flush=True)
                content=fetch_once(url,timeout=20)
                with open(out,"wb") as f: f.write(content)
                results.append({"url":url,"file":f"page_{i}.html","size":len(content),"status":"success"})
                ok=True; break
            except Exception as e:
                err=e; time.sleep(1.5)
        if not ok:
            results.append({"url":url,"file":None,"error":str(err),"status":"failed"})

    status={
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "urls_processed":len(urls),
        "successful":sum(r["status"]=="success" for r in results),
        "failed":sum(r["status"]=="failed" for r in results),
        "results":results
    }
    with open("/shared/status/fetch_complete.json","w") as f: json.dump(status,f,indent=2)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Fetcher done",flush=True)

if __name__=="__main__":
    main()
