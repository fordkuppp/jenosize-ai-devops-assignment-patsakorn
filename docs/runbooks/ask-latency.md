# Runbook — /ask latency budget burning

**Alert:** `JenieAskLatency` · **SLO:** 99% of `/ask` under 3s over 30d

## Split the budget first

End-to-end latency is retrieval plus generation. Check which one moved before
anything else:

```promql
histogram_quantile(0.95, sum(rate(rag_retrieval_duration_seconds_bucket[5m])) by (le, stage))
histogram_quantile(0.95, sum(rate(rag_generation_duration_seconds_bucket[5m])) by (le))
```

If retrieval moved, `JenieRetrievalLatency` should also be firing — work that
runbook instead; this one is a symptom of it.

## If generation moved

The platform does not control model latency, which is why it has its own SLI.
Check queue depth and concurrency at the backend. Batching helps throughput,
not tail latency — raising concurrency without raising replicas usually makes
p95 worse.

## If neither moved

Latency is in the gateway or in queuing. Check Envoy:

```sh
kubectl -n envoy-gateway-system logs -l app.kubernetes.io/name=envoy --tail=100
```

Saturation shows up as `maxPendingRequests` rejections before it shows up as
latency — check the circuit breaker counters.

## Note on buckets

The SLI counts requests under the `le="3.0"` bucket. If someone changes the
histogram buckets without changing this SLO, the alert silently starts
measuring a different threshold.
