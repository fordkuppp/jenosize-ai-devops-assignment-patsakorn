#!/usr/bin/env python3
"""Retrieval evaluation.

Runs the query set against a live /ask and asserts the expected document was
cited. Exits non-zero on regression, so it can gate a pipeline.

It measures retrieval, not fluency. Asserting on generated text would test
whichever model happens to be behind LLM_BASE_URL; asserting on the citation
tests the index, the chunking and the ranking — the parts this platform owns
and the parts that actually break.
"""

import argparse
import json
import pathlib
import statistics
import sys
import time

import httpx
import yaml


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--queries", default="scripts/queries.yaml")
    ap.add_argument("--min-pass-rate", type=float, default=0.8)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    cases = yaml.safe_load(pathlib.Path(args.queries).read_text())
    results, latencies = [], []

    with httpx.Client(timeout=60.0) as client:
        for case in cases:
            started = time.perf_counter()
            try:
                r = client.post(f"{args.url}/ask", json={"query": case["query"]})
                r.raise_for_status()
                body = r.json()
                err = None
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                body, err = {"sources": [], "latency_ms": 0}, str(exc)
            wall = (time.perf_counter() - started) * 1000
            latencies.append(wall)

            cited = [s["path"] for s in body.get("sources", [])]
            want = case.get("expect_source")
            rank = None
            if err:
                ok, why = False, err
            elif want is None:
                # Refusal case: citing anything means it answered from
                # documents that do not contain the answer.
                ok = len(cited) == 0
                why = "declined" if ok else f"should have declined, cited {cited}"
            else:
                # Rank matters. The generated answer quotes the top chunk, so
                # "somewhere in the top 5" is recall and only rank 1 means the
                # user actually got the right passage. Reporting the first
                # citation as if it were the match hid a wrong answer that
                # still passed.
                rank = cited.index(want) + 1 if want in cited else 0
                ok = rank > 0
                why = (
                    f"rank {rank}" + ("" if rank == 1 else f" — top was {cited[0]}")
                    if ok
                    else f"wanted {want}, got {cited or 'nothing'}"
                )

            results.append(
                {"id": case["id"], "ok": ok, "rank": rank,
                 "detail": why, "latency_ms": body.get("latency_ms", 0),
                 "wall_ms": round(wall)}
            )

    passed = sum(r["ok"] for r in results)
    rate = passed / len(results)
    ranked = [r for r in results if r.get("rank")]
    at1 = sum(1 for r in ranked if r["rank"] == 1)
    p_at_1 = at1 / len(ranked) if ranked else 1.0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0]
    summary = {
        "passed": passed,
        "total": len(results),
        "pass_rate": round(rate, 3),
        "precision_at_1": round(p_at_1, 3),
        "p95_ms": round(p95),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for r in results:
            status = "PASS" if r["ok"] else "FAIL"
            print(f"  {status}  {r['id']:28} {r['wall_ms']:>5}ms  {r['detail']}")
        print(
            f"\n{passed}/{len(results)} passed ({rate:.0%}), "
            f"precision@1 {at1}/{len(ranked)} ({p_at_1:.0%}), p95 {p95:.0f}ms"
        )

    if rate < args.min_pass_rate:
        print(f"\nFAILED: pass rate {rate:.0%} below {args.min_pass_rate:.0%}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
