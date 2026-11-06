#!/usr/bin/env python3
"""Evaluation harness.

Runs the query set against a live /ask and reports retrieval correctness plus
latency. Exits non-zero below the pass threshold so CI can gate on it.

    python3 scripts/eval.py [--url http://localhost:8080] [--threshold 0.8]
"""

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

QUERIES = Path(__file__).parent / "queries.yaml"


def ask(url: str, query: str, timeout: float) -> tuple[dict, float]:
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        f"{url}/ask", data=body, headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    return payload, (time.perf_counter() - start) * 1000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()

    cases = yaml.safe_load(QUERIES.read_text())
    latencies: list[float] = []
    passed = 0

    print(f"{'result':<8}{'ms':>8}  query")
    print("-" * 72)

    for case in cases:
        want = case.get("expect_source") or ""
        try:
            payload, ms = ask(args.url, case["query"], args.timeout)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"{'ERROR':<8}{'-':>8}  {case['query']}  ({exc})")
            continue

        latencies.append(ms)
        titles = " ".join(s.get("title", "") for s in payload.get("sources", []))

        # An out-of-scope query passes by citing nothing, not by guessing.
        ok = (want in titles) if want else not payload.get("sources")
        passed += ok
        print(f"{'PASS' if ok else 'FAIL':<8}{ms:>8.0f}  {case['query']}")

    total = len(cases)
    rate = passed / total if total else 0.0
    print("-" * 72)
    print(f"pass {passed}/{total} ({rate:.0%})")
    if latencies:
        print(f"latency  mean {statistics.mean(latencies):.0f}ms  "
              f"p95 {sorted(latencies)[int(len(latencies) * 0.95) - 1]:.0f}ms")

    return 0 if rate >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
