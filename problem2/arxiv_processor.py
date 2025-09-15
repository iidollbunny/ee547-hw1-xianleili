#!/usr/bin/env python3
"""
EE547 - Problem 2: ArXiv Paper Metadata Processor
Uses only Python standard libraries.
"""

import sys
import os
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

ARXIV_ENDPOINT = "http://export.arxiv.org/api/query"

# Stopwords provided in the assignment
STOPWORDS = { ... }  # keep same content

def utc_now_iso() -> str:
    # Return current UTC time in ISO-8601 format
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log_line(log_path: str, message: str) -> None:
    # Append one log line to processing.log
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] {message}\n")

def fetch_with_retries(url: str, headers=None, max_retries=3, sleep_seconds=3) -> bytes:
    # Fetch URL with retry on HTTP 429 (rate limiting)
    attempt = 0
    while True:
        attempt += 1
        try:
            req = Request(url, headers=headers or {"User-Agent": "ee547-arxiv-processor"})
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                time.sleep(sleep_seconds)
                continue
            raise
        except URLError:
            raise

def parse_atom(xml_bytes: bytes, log_path: str):
    # Parse Atom XML and extract metadata for each paper
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        log_line(log_path, f"ERROR Invalid XML: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("atom:entry", ns):
        try:
            id_full = entry.findtext("atom:id", default="", namespaces=ns)
            arxiv_id = id_full.rsplit("/", 1)[-1]
            title = entry.findtext("atom:title", default="", namespaces=ns).strip()
            summary = entry.findtext("atom:summary", default="", namespaces=ns).strip()
            published = entry.findtext("atom:published", default="", namespaces=ns).strip()
            updated = entry.findtext("atom:updated", default="", namespaces=ns).strip()
            authors = [a.findtext("atom:name", default="", namespaces=ns).strip()
                       for a in entry.findall("atom:author", ns)]
            categories = [c.attrib.get("term", "").strip()
                          for c in entry.findall("atom:category", ns)]

            # Skip if required fields are missing
            if not (arxiv_id and title and summary and published and updated and authors and categories):
                raise ValueError("missing required field(s)")

            entries.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "abstract": summary,
                "categories": categories,
                "published": published,
                "updated": updated
            })
        except Exception as e:
            log_line(log_path, f"WARNING Skipping paper due to missing/invalid fields: {e}")
    return entries

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENT_SPLIT_RE = re.compile(r"[\.!?]+")

def tokenize_words(text: str):
    # Return all words in the text
    return WORD_RE.findall(text)

def word_stats(text: str):
    # Compute word count, unique words, top 20 terms, average length
    words = tokenize_words(text)
    total = len(words)
    if total == 0:
        return {
            "total_word_count": 0,
            "unique_word_count": 0,
            "top_20_terms": [],
            "avg_word_length": 0.0
        }
    counts = {}
    total_len = 0
    for w in words:
        total_len += len(w)
        wlwr = w.lower()
        if wlwr in STOPWORDS:
            continue
        counts[wlwr] = counts.get(wlwr, 0) + 1
    top20 = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    avg_len = total_len / total if total else 0.0
    return {
        "total_word_count": total,
        "unique_word_count": len(counts),
        "top_20_terms": top20,
        "avg_word_length": round(avg_len, 3)
    }

def sentence_stats(text: str):
    # Compute sentence statistics based on punctuation
    s = re.sub(r"\s+", " ", text.strip())
    parts = [p.strip() for p in SENT_SPLIT_RE.split(s) if p.strip()]
    if not parts:
        return {
            "total_sentence_count": 0,
            "avg_words_per_sentence": 0.0,
            "longest_sentence_words": 0,
            "shortest_sentence_words": 0
        }
    lens = [len(tokenize_words(p)) for p in parts]
    avg = sum(lens) / len(parts) if parts else 0.0
    return {
        "total_sentence_count": len(parts),
        "avg_words_per_sentence": round(avg, 3),
        "longest_sentence_words": max(lens),
        "shortest_sentence_words": min(lens)
    }

def technical_terms(text: str):
    # Extract uppercase, numeric, and hyphenated terms
    tokens = re.findall(r"[A-Za-z0-9\-]+", text)
    upper = sorted({t for t in tokens if any(c.isupper() for c in t)})
    numeric = sorted({t for t in tokens if any(c.isdigit() for c in t)})
    hyphen = sorted({t for t in tokens if "-" in t and len(t) > 1})
    return {
        "uppercase_terms": upper,
        "numeric_terms": numeric,
        "hyphenated_terms": hyphen
    }

def analyze_abstract(abstract: str):
    # Perform word, sentence, and technical term analysis
    return {
        "word_frequency": word_stats(abstract),
        "sentence_analysis": sentence_stats(abstract),
        "technical_terms": technical_terms(abstract)
    }

def main():
    # Parse command-line arguments
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <search_query> <max_results 1..100> <output_dir>", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    max_results = int(sys.argv[2])
    output_dir = sys.argv[3]
    os.makedirs(output_dir, exist_ok=True)

    # Paths for output files
    papers_json_path = os.path.join(output_dir, "papers.json")
    stats_json_path = os.path.join(output_dir, "stats.json")
    log_path = os.path.join(output_dir, "processing.log")

    # Log start
    t0 = time.time()
    log_line(log_path, f"Starting ArXiv query: {query}")

    # Build query URL
    params = {"search_query": query, "start": 0, "max_results": max_results}
    url = f"{ARXIV_ENDPOINT}?{urlencode(params)}"

    # Fetch XML from ArXiv
    try:
        xml_bytes = fetch_with_retries(url)
    except (HTTPError, URLError) as e:
        log_line(log_path, f"ERROR Network error: {e}")
        sys.exit(1)

    # Parse XML response
    entries = parse_atom(xml_bytes, log_path)
    log_line(log_path, f"Fetched {len(entries)} results from ArXiv API")

    # Write metadata to papers.json
    with open(papers_json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # Analyze abstracts and write to stats.json
    stats = {
        "query": query,
        "generated_at_utc": utc_now_iso(),
        "total_papers": len(entries),
        "papers": []
    }
    for p in entries:
        log_line(log_path, f"Processing paper: {p['arxiv_id']}")
        stats["papers"].append({"arxiv_id": p["arxiv_id"], **analyze_abstract(p["abstract"])})

    with open(stats_json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Log completion
    elapsed = time.time() - t0
    log_line(log_path, f"Completed processing: {len(entries)} papers in [{elapsed:.2f}] seconds")

if __name__ == "__main__":
    main()
