# Decisions

What was built, what was deliberately not, and where this is more platform
than the brief asked for.

---

## The honest summary first

The brief says *choose one* of Terraform, Kubernetes manifests, or Pulumi. It
says dev/prod separation *can be minimal*, that *VPC or k8s namespaces* is
enough, that *one* deployment strategy is required, that *at least two*
alerts will do, and that a DR *outline is ok*.

This repository does Terraform **and** manifests **and** GitOps, runs two
clusters, implements canary with automated rollback, generates twelve alerts,
and has a tested backup. It runs seven controllers. The brief strictly
requires none of them.

Each decision below is defensible on its own. Cumulatively they are more
system than the exercise called for, and a smaller team should cut several.
Where that applies it is said in the entry.

---

## Gateway API, not Ingress

**Decision.** Routing is Gateway API implemented by Envoy Gateway.

**Why.** Kubernetes SIG Network retired Ingress NGINX in March 2026, and
InGate — its intended successor — was retired alongside it. Reaching for
ingress-nginx in November 2026 is not a conservative choice; it is a finding.

**Cost.** Gateway API is less familiar and the ecosystem is thinner. Envoy's
`BackendTrafficPolicy` turned out to be a benefit: rate limiting and circuit
breaking as typed, validated configuration rather than annotation strings.

---

## A mesh was considered and rejected

**Decision.** No service mesh.

**Why.** Istio ambient would cover north-south and east-west in one install.
But this architecture has two workloads and a database: the internal hops are
`api → postgres` and `indexer → postgres`, and CNPG already does TLS. A mesh
here is cost without a threat it mitigates.

**When that changes.** Around a dozen services, or when workload identity has
to be enforced between teams rather than assumed.

---

## Terraform *and* GitOps, with a hard boundary

**Decision.** Terraform owns the cluster, the SOPS key and the deploy key.
Flux owns everything else.

**Why.** The division is "what can Flux read from git". Flux cannot bootstrap
itself or decrypt without a key, so those come from Terraform. Everything
else is reconciled, which is what makes `make up-<env>` a complete recovery
procedure.

**Cost.** Two tools instead of one. The brief would have accepted either
alone.

**Two stages, not one.** The Kubernetes provider validates `config_path`
during *plan*, so a root module that creates a cluster and configures a
provider from its kubeconfig fails before creating anything. Configuring the
provider from the cluster resource instead is a dependency cycle. This was
learned by doing it the wrong way first.

---

## Two clusters rather than two namespaces

**Decision.** `jenie-dev` and `jenie-prod` are separate kind clusters.

**Why (originally).** Namespaces do not isolate CRDs, controllers or
cluster-scoped policy, so a namespace-only split cannot demonstrate that a
change is safe before it reaches production.

**Why (actually).** The original reason is theoretical. The real one is
empirical: two defects were found that dev structurally could not surface.
`analysis.maxRetries` was an invented Flagger field, and only prod renders a
Canary. The API held a single database connection that never recovered, and
only prod has three PostgreSQL instances that roll. Both would have shipped.

**Cost.** Roughly 6–8 GB of memory and double the reconcile time. **Cut this
first** if resources are tight — but know that it is what caught those two.

---

## Flagger, not a rolling update

**Decision.** Production deploys as a canary with automatic rollback.

**Why.** The brief allows rolling-with-health-checks, which is free. Flagger
was chosen for one reason: `rag-refusal-rate` as a release gate. A release
that starts refusing questions it used to answer returns HTTP 200 quickly and
is invisible to error rate and latency. No HTTP-level signal catches a broken
index or a bad prompt; a retrieval-aware one does.

**Cost.** Two controllers, and `flagger-loadtester` is mandatory rather than
optional — without synthetic traffic, analysis gathers no samples and stalls
instead of failing.

**If cutting.** Rolling update with probes satisfies the brief. The gate is
the part worth keeping, and it could be an alert instead.

---

## Sloth, not hand-written alerts

**Decision.** SLOs are declared; the alerts are generated.

**Why.** Three objectives produce 45 recording rules and 6 multi-window
multi-burn-rate alerts. Hand-writing four burn-rate windows across two SLIs
is eight fiddly rules that drift from the objective they claim to defend.
Declaring the objective keeps them honest.

**Cost.** One more controller, and the chart is **vendored** because Sloth
publishes only as a GitHub release asset with no mirror. One unreachable
download left a cluster with no ingress — `wait: true` means a HelmRelease
that cannot pull blocks everything behind it.

**If cutting.** The brief asks for two alerts. Two hand-written rules are a
tenth of the effort.

---

## Alerts in Prometheus, not Grafana

**Decision.** `PrometheusRule`, evaluated by Prometheus.

**Why.** Grafana's own guidance prefers Grafana-managed rules, so this needs
justifying. Sloth only emits PrometheusRule; burn-rate alerts depend on
recording rules Grafana cannot create; and alerting should depend on as
little as possible — Grafana-managed rules evaluate inside Grafana, making it
a hard dependency for paging.

**When that changes.** When a rule needs two data sources. "Error rate up
**and** this log pattern appeared" is not expressible in Prometheus. Those
rules would be Grafana-managed and route to the same Alertmanager — one
router, always.

---

## A policy chart that owns no workload

**Decision.** `service-policy` renders routing, traffic policy, progressive
delivery, network policy, autoscaling and monitoring wiring. The Deployment
and Service are plain manifests.

**Why.** The first attempt was a generic workload chart — a `podTemplate`
pass-through with one consumer. That is `app-template` rebuilt worse. The pod
layer has good tooling; the policy layer does not, and that is where a new
service needs help on day one.

**Cost.** ~950 lines for one consumer. A generic abstraction with one
consumer is premature by definition, and this is the entry a reviewer is most
entitled to push back on. The counter-argument is that the *second* service
is where it pays, and the brief asks for a clear scaling story.

---

## Backups implemented, not outlined

**Decision.** Continuous WAL archiving plus daily base backups through the
barman-cloud plugin, with a documented restore.

**Why.** Everything stateless is recoverable with `make up-<env>` — the
repository *is* the backup, and that path has been exercised repeatedly. That
reduction only holds if the one stateful component is genuinely covered.

**Cost.** cert-manager, the plugin, and an object store. The brief said an
outline was enough. **This is the clearest over-build**, and it was done
because the conversation asked for it rather than because the exercise
required it.

**The plugin, not `spec.backup.barmanObjectStore`.** The in-tree path still
works in CNPG 1.30 but was deprecated in 1.26 with removal announced.
Deprecated-but-working is exactly where ingress-nginx was.

---

## Real embeddings, stubbed model

**Decision.** `BAAI/bge-small-en-v1.5` baked into the image; the LLM is a
deterministic stub unless `LLM_BASE_URL` is set.

**Why.** The brief permits mocking the LLM and says nothing about embeddings.
Mocking embeddings would make retrieval meaningless, and retrieval is the
half a platform actually owns. The stub is **extractive** — it quotes the
retrieved passage rather than paraphrasing, so every evaluation result is
attributable to retrieval instead of hidden behind plausible prose.

**Cost.** 701 MB images, mostly onnxruntime and the model. It buys no runtime
download, no egress requirement and a read-only root filesystem.

---

## Hybrid retrieval, and why RRF alone is not enough

**Decision.** pgvector HNSW plus a generated `tsvector`, fused with
Reciprocal Rank Fusion, with raw cosine similarity carried alongside.

**Why.** Operations questions are full of literals — `externalTrafficPolicy`,
`postInitApplicationSQL` — that embeddings blur. RRF needs no score
calibration between retrievers, which is its appeal.

**The catch.** RRF is rank-based, so it discards how good the best match
was: a nonsense query still produces a rank-1 result with a high fused score.
Refusal therefore gates on cosine similarity, not on the fused score. Without
that the service cannot distinguish "best match" from "good match", and will
answer anything.

---

## What is still missing

- **No Grafana dashboard.** The brief lists one. Metrics, alerts and
  recording rules exist; the visualisation does not.
- **No `docker compose up` path.** The brief offers it as an alternative to a
  deployed URL and its "what great looks like" list opens with it. `make
  up-dev` is a third thing — more capable, and more to install.
- **CI does not build or deploy images.** It lints, tests, scans and
  validates. There is no image build job and no end-to-end job.
- **The LLM has never been real.** vLLM behind `LLM_BASE_URL` would need no
  code change, and has not been demonstrated.

---

## What this cost

Nineteen defects were found during this work. Of those, **none** were caught
by `make validate` — rendering and schema checks only ever confirmed what was
already believed. Eleven needed a running cluster, four needed re-reading the
code with fresh eyes, one needed a server-side dry run against a live API
server, and one needed reading controller logs rather than status.

That distribution is the most useful thing learned here, and it is why
`make verify` exists alongside `make validate`, and why both clusters get
built from scratch rather than iterated on.
