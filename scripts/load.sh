#!/usr/bin/env bash
# Concurrency demo: fire N requests at /ask with C in flight.
#
# The point is not throughput for its own sake. With a batching inference server
# (vLLM) behind it, you should see latency stay roughly flat as concurrency
# rises until the batch saturates — then climb. That curve is the story.
set -euo pipefail

URL="${URL:-http://localhost:8080/ask}"
N="${N:-100}"
C="${C:-10}"
QUERY="${QUERY:-How do I check why a pod is pending?}"

echo "sending $N requests, $C concurrent, to $URL"
seq "$N" | xargs -P "$C" -I{} \
  curl -s -o /dev/null -w '%{time_total}\n' \
    -X POST "$URL" \
    -H 'Content-Type: application/json' \
    -d "{\"query\": \"${QUERY}\"}" \
  | sort -n | awk '
      { t[NR] = $1; sum += $1 }
      END {
        printf "n=%d  mean=%.3fs  p50=%.3fs  p95=%.3fs  max=%.3fs\n",
               NR, sum/NR, t[int(NR*0.50)], t[int(NR*0.95)], t[NR]
      }'
