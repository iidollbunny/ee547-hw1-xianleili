#!/usr/bin/env python3
import json, os, re, time
from collections import Counter
from datetime import datetime, timezone
from glob import glob
from itertools import combinations

STATUS_PROCESS="/shared/status/process_complete.json"
STOPWORDS=set("a an and are as at be by for from has have in is it its of on or that the this to was were will with".split())

def tokenize(text): return [w for w in re.findall(r"[a-z]+",text.lower()) if w not in STOPWORDS]
def ngrams(tokens,n): return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
def jaccard(a,b): return len(a&b)/len(a|b) if a|b else 0.0

def readability(all_tokens,sents):
    tot=sum(len(t) for t in all_tokens); uniq=len(set(sum(all_tokens,[])))
    tot_sent=sum(sents)
    avg_sent=tot/tot_sent if tot_sent else 0.0
    avg_word=(sum(len(w) for t in all_tokens for w in t)/tot) if tot else 0.0
    comp=uniq/tot if tot else 0.0
    return {"avg_sentence_length":round(avg_sent,4),"avg_word_length":round(avg_word,4),"complexity_score":round(comp,4)}

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Analyzer start",flush=True)
    while not os.path.exists(STATUS_PROCESS):
        print("Waiting for process_complete.json ...",flush=True); time.sleep(2)

    os.makedirs("/shared/analysis",exist_ok=True)
    processed=sorted(glob("/shared/processed/*.json"))

    if not processed:
        report={"processing_timestamp":datetime.now(timezone.utc).isoformat(),
                "documents_processed":0,"total_words":0,"unique_words":0,
                "top_100_words":[],"document_similarity":[],"top_bigrams":[],"top_trigrams":[],
                "readability":{"avg_sentence_length":0.0,"avg_word_length":0.0,"complexity_score":0.0}}
        with open("/shared/analysis/final_report.json","w") as f: json.dump(report,f,indent=2)
        print("Analyzer: no processed documents. Wrote empty report.",flush=True)
        return

    docs=[]; names=[]; sents=[]
    for p in processed:
        with open(p) as f: d=json.load(f)
        text=d.get("text",""); toks=tokenize(text)
        docs.append(toks); names.append(os.path.basename(p))
        sc=d.get("statistics",{}).get("sentence_count",0)
        if not sc: sc=max(1,text.count(".")+text.count("!")+text.count("?"))
        sents.append(sc)

    counter=Counter(); [counter.update(t) for t in docs]
    top100=[{"word":w,"count":c,"frequency":round(c/sum(counter.values()),6)} for w,c in counter.most_common(100)]

    sim=[{"doc1":names[i],"doc2":names[j],"similarity":round(jaccard(set(docs[i]),set(docs[j])),6)} for i,j in combinations(range(len(docs)),2)]

    big=Counter(); tri=Counter()
    for t in docs: big.update(ngrams(t,2)); tri.update(ngrams(t,3))
    top_b=[{"bigram":bg,"count":c} for bg,c in big.most_common(50)]
    top_t=[{"trigram":tg,"count":c} for tg,c in tri.most_common(50)]

    report={"processing_timestamp":datetime.now(timezone.utc).isoformat(),
            "documents_processed":len(processed),
            "total_words":sum(len(t) for t in docs),
            "unique_words":len(set(sum(docs,[]))),
            "top_100_words":top100,
            "document_similarity":sim,
            "top_bigrams":top_b,
            "top_trigrams":top_t,
            "readability":readability(docs,sents)}

    with open("/shared/analysis/final_report.json","w") as f: json.dump(report,f,indent=2)
    with open("/shared/status/analyze_complete.json","w") as f: json.dump({"timestamp":datetime.now(timezone.utc).isoformat()},f,indent=2)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Analyzer done",flush=True)

if __name__=="__main__":
    main()
