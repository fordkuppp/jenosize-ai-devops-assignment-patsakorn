# Runbook — retrieval latency budget burning

**Alert:** `JenieRetrievalLatency` · **SLO:** 99% of retrievals under 500ms

Retrieval is the part of `/ask` the platform owns, which is why it is a
separate SLO: a slow model should not burn the budget for a slow index.

## Confirm which stage

```promql
histogram_quantile(0.95, sum(rate(rag_retrieval_duration_seconds_bucket[5m])) by (le, stage))
```

- `stage="embed"` — the embedding model, not the database
- `stage="search"` — pgvector
- `stage="rerank"` — if enabled

## If search

```sh
kubectl -n jenie get cluster jenie-pg -o wide
kubectl -n jenie exec -it jenie-pg-1 -- psql -U jenie -c "\di+"
```

Most common cause is a missing or unused vector index after a reindex — an
HNSW index has to be built, and a fresh table will sequential-scan happily and
correctly, just slowly. Check `rag_index_documents` against what you expect:
a corpus that grew by an order of magnitude will do this.

Second most common: connection saturation. CNPG exposes
`cnpg_backends_total`; compare against `max_connections` (100).

## If embed

The embedding model runs in-process. Check CPU throttling on the pod — the
container has a 1 CPU limit, and embedding is the one thing that will hit it.

## Mitigate

Retrieval degradation does not require a rollback. Lower `RETRIEVAL_TOP_K` in
the ConfigMap to cut work per request while you investigate.
