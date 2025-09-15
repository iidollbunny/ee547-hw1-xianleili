#!/usr/bin/env python3
# Problem 1 - Part A: HTTP fetcher (standard library only)

import sys
import os
import json
import re
import time
import datetime
from urllib import request, error

# ISO-8601 UTC format with 'Z'
ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

def utc_now_iso() -> str:
    # Return current UTC time as ISO-8601 string
    return datetime.datetime.utcnow().strftime(ISO_FMT)

# Regex to detect "words" in text (letters/numbers)
_word_re = re.compile(r"[A-Za-z0-9]+")

def is_text_content(content_type: str | None) -> bool:
    # Decide if Content-Type header indicates text
    if not content_type:
        return False
    return "text" in content_type.lower()

def extract_charset(content_type: str | None) -> str | None:
    # Try to extract charset from Content-Type header
    if not content_type:
        return None
    ct = content_type.lower()
    if "charset=" in ct:
        try:
            return ct.split("charset=")[-1].split(";")[0].strip()
        except Exception:
            return None
    return None

def count_words_from_bytes(body: bytes, preferred_encoding: str | None) -> int:
    # Decode response body into text and count words
    enc_candidates = []
    if preferred_encoding:
        enc_candidates.append(preferred_encoding)
    enc_candidates += ["utf-8", "latin-1"]

    text = None
    for enc in enc_candidates:
        try:
            text = body.decode(enc, errors="ignore")
            break
        except Exception:
            continue
    if text is None:
        return 0
    return len(_word_re.findall(text))

def fetch_one(url: str, timeout_sec: float = 10.0) -> dict:
    # Fetch a single URL and collect metrics
    started = time.perf_counter()
    ts = utc_now_iso()
    rec: dict = {
        "url": url,
        "status_code": None,
        "response_time_ms": None,
        "content_length": 0,
        "word_count": None,
        "timestamp": ts,
        "error": None,
    }
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read()
            elapsed_ms = (time.perf_counter() - started) * 1000.0

            status = getattr(resp, "status", None) or resp.getcode()
            ctype = resp.headers.get("Content-Type", "")
            clen = len(body)
            charset = extract_charset(ctype)

            rec["status_code"] = int(status)
            rec["response_time_ms"] = float(elapsed_ms)
            rec["content_length"] = int(clen)

            # Only count words for textual content
            if is_text_content(ctype):
                rec["word_count"] = int(count_words_from_bytes(body, charset))
            else:
                rec["word_count"] = None

    except Exception as ex:
        # Handle network/timeout/invalid URL errors
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rec["response_time_ms"] = float(elapsed_ms)
        rec["error"] = str(ex)

    return rec

def main():
    # Verify arguments: must have input file and output dir
    if len(sys.argv) != 3:
        print(f"Usage: {os.path.basename(sys.argv[0])} <input_file> <output_directory>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    # Read all URLs from input file
    with open(input_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    # Start processing
    processing_start = utc_now_iso()
    responses: list[dict] = [fetch_one(u, timeout_sec=10.0) for u in urls]
    processing_end = utc_now_iso()

    # Save detailed responses.json
    with open(os.path.join(output_dir, "responses.json"), "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

    # Build summary.json
    total_urls = len(responses)
    successful = 0
    failed = 0
    total_bytes = 0
    times_ms: list[float] = []
    status_dist: dict[str, int] = {}

    for r in responses:
        code = r["status_code"]
        err = r["error"]
        rt = r["response_time_ms"]
        if isinstance(rt, (int, float)):
            times_ms.append(float(rt))

        if err is not None or code is None or not (200 <= int(code) <= 399):
            failed += 1
        else:
            successful += 1
            total_bytes += int(r.get("content_length", 0))

        k = str(int(code)) if code is not None else "ERR"
        status_dist[k] = status_dist.get(k, 0) + 1

    avg_ms = (sum(times_ms) / len(times_ms)) if times_ms else 0.0
    summary = {
        "total_urls": total_urls,
        "successful_requests": successful,
        "failed_requests": failed,
        "average_response_time_ms": avg_ms,
        "total_bytes_downloaded": total_bytes,
        "status_code_distribution": status_dist,
        "processing_start": processing_start,
        "processing_end": processing_end,
    }
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Save errors.log (only failed requests)
    err_lines = [f"[{r['timestamp']}] [{r['url']}]: {r['error']}" for r in responses if r["error"]]
    with open(os.path.join(output_dir, "errors.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(err_lines))

if __name__ == "__main__":
    main()
