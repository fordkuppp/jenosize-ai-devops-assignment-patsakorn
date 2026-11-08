# Observability

Metrics come from kube-prometheus-stack. The application exposes Prometheus
metrics on `/metrics`, scraped by a PodMonitor.

## Why a PodMonitor and not a ServiceMonitor

Under Flagger the Service set churns during a rollout — apex, `-primary` and
`-canary` appear and disappear — so a Service-based scrape either misses
canary pods or double counts them. Pod labels stay stable, and canary metrics
have to remain distinguishable for the analysis to mean anything.

## Application metrics

| metric | meaning |
|---|---|
| `rag_retrieval_duration_seconds{stage}` | embed and search timed separately |
| `rag_generation_duration_seconds{model}` | time in the model call |
| `rag_request_duration_seconds{model}` | end to end `/ask` |
| `rag_documents_retrieved` | chunks returned per query |
| `rag_retrieval_score` | best similarity — the drift signal |
| `rag_tokens_total{kind,model}` | prompt and completion tokens |
| `rag_cost_usd_total{model}` | simulated spend |
| `rag_answers_total{outcome}` | answered, refused, no_context |
| `rag_errors_total{stage}` | failures by pipeline stage |
| `rag_index_documents` | chunks currently indexed |
| `rag_index_last_success_timestamp_seconds` | indexer freshness |

Retrieval and generation are separate because the platform owns one and the
model owns the other. Blended into a single duration you cannot tell a slow
vector search from a slow model, which is the first question anyone asks.

## Histogram buckets are a contract

Every threshold in an SLO must exist as a bucket boundary. Prometheus cannot
interpolate between buckets: a query for `le="3.0"` against a histogram
without that boundary matches no series, the ratio evaluates to nothing, and
the objective reports healthy while measuring nothing at all.

The buckets are declared in `jenie/telemetry.py` and the thresholds in
`slo.yaml`. They are one decision, not two.

## Disabled default alerts

kube-prometheus-stack ships roughly a hundred alerts tuned for a managed
cluster. Several fire permanently on kind — `KubeControllerManagerDown`,
`KubeSchedulerDown` and `KubeProxyDown` bind to 127.0.0.1 under kubeadm and
cannot be scraped; overcommit is the normal state of a single-node cluster.
They are disabled explicitly, each with a reason. A dashboard with twelve
permanently red alerts is worse than no alerting, because it trains everyone
to ignore the page.
