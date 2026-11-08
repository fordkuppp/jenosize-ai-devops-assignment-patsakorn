# Progressive delivery

Production deploys as a Flagger canary. Dev uses a plain rolling update.

## How a canary progresses

Flagger takes over the Deployment, creating `-primary` and `-canary`
variants plus the HTTPRoute, and shifts traffic in steps. Production moves
20% at a time to a maximum of 60%, evaluating every 30 seconds. Three failed
checks roll the release back automatically.

Rolling update is not an alternative to this — it is the inner mechanism.
`maxSurge` and `maxUnavailable` govern how the primary itself rolls once a
canary is promoted.

## What gates a release

Two signals come from Envoy: request success rate must stay at or above 99%,
and request duration at or below 3000ms.

The third is specific to this service: `rag-refusal-rate` must stay at or
below 40%. A release that starts refusing questions it used to answer returns
HTTP 200 quickly, so it is invisible to both error rate and latency. Nothing
except a retrieval-aware metric catches a broken index or a bad prompt.

## The load tester is mandatory

Canary analysis evaluates metrics over a window. With no traffic there are no
samples, so the rollout neither passes nor fails — it stalls until the
progress deadline. `flagger-loadtester` generates synthetic traffic against
the `-canary` service during analysis. Pointing it at the stable service
instead measures the old version and always passes.

## Rollback

Flagger rolls back automatically on a failed analysis. For a release that
applied cleanly but is wrong, revert the commit — Flux reconciles within a
minute. Do not use `kubectl edit`; it will be reverted and you will lose time
wondering why.
