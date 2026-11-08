# SLOs and alerting

Objectives are declared as Sloth `PrometheusServiceLevel` resources. Sloth
generates the recording rules and multi-window multi-burn-rate alerts from
them — 45 recording rules and 6 alerts from three objectives.

## The objectives

| SLO | objective | window |
|---|---|---|
| `ask-availability` | 99% of `/ask` non-5xx | 30 days |
| `ask-latency` | 99% of `/ask` under 2.5s | 30 days |
| `retrieval-latency` | 99% of retrievals under 500ms | 30 days |

Retrieval has its own objective because it is the part the platform
controls. A slow model should not burn the budget for a slow index, and
splitting them tells you which regressed.

## Burn rate, not thresholds

Each objective produces a page alert and a ticket alert. The page fires on
fast burn — at that rate the 30-day budget is gone in hours. The ticket fires
on slow burn: real, but it can wait for working hours. A blip the error
budget can absorb pages nobody.

## Alerts that are not SLOs

Not everything worth alerting on is user-facing reliability with an error
budget. These are hand-written because forcing them into an SLO would
produce a burn rate that means nothing:

- `JenieIndexStale` — no successful index in 24h
- `JenieIndexEmpty` — the vector store has no chunks
- `JenieCostPerRequestSpike` — hourly cost per request above twice the daily baseline
- `JenieRefusalRateHigh` — more than 30% refusals sustained
- `JenieGatewayNoHealthyBackends` — Envoy has zero healthy endpoints
- `JenieCanaryStuck` — analysis running for over 30 minutes

`JenieGatewayNoHealthyBackends` covers the blind spot the others share: they
all measure requests, and zero healthy backends means zero requests, so error
rate and latency both stay clean while the service is down.

## Where alerts live

In Prometheus, not Grafana. Alerting should depend on as little as possible,
and Grafana-managed rules evaluate inside Grafana. `PrometheusRule` is also a
CRD, so Flux reconciles it and CI schema-checks it like everything else.

Grafana-managed rules become the right answer when a rule needs two data
sources — "error rate up and this log pattern appeared" is something
Prometheus cannot express. They would route to the same Alertmanager.
