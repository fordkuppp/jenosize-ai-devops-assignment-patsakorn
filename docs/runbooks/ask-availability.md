# Runbook — /ask availability budget burning

**Alert:** `JenieAskAvailability` · **SLO:** 99% of `/ask` non-5xx over 30d

A page means fast burn: at this rate the 30-day budget is gone in hours.
A ticket means slow burn — real, but it can wait for working hours.

## Confirm

```sh
kubectl -n jenie get canary,pods
kubectl -n jenie logs -l app.kubernetes.io/name=jenie-api --tail=100 | grep -i error
```

Check Grafana → Jenie → error rate by `status` and by `stage`. The
`rag_errors_total{stage}` label says which part failed: `embed`, `search` or
`generate`.

## Likely causes, cheapest first

| Symptom | Cause | Action |
|---|---|---|
| errors start at a deploy | bad release | `kubectl -n jenie describe canary jenie-api` — if a canary is mid-analysis Flagger will roll back on its own; do not intervene |
| `stage="search"` | Postgres unavailable or slow | `kubectl -n jenie get cluster jenie-pg` |
| `stage="generate"` | model backend down | check `LLM_BASE_URL`; the stub should never fail |
| all stages, all pods | gateway or DNS | see `JenieGatewayNoHealthyBackends` |

## Mitigate

Roll back to the last known-good tag by reverting the image tag commit in
`kubernetes/apps/jenie/`. Flux reconciles within a minute. Do **not**
`kubectl edit` — it will be reverted, and you will lose time wondering why.

## Escalate

If the budget is exhausted, freeze deploys (pause the Flux Kustomization)
before investigating further.
