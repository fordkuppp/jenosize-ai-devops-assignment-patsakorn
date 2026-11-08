# Security

Posture and threat assumptions for Jenie Helpdesk AI. This describes what is
actually implemented, and is explicit about what is not.

## What this is defending

A single-tenant internal help desk over public operations documentation. The
corpus contains no secrets and no customer data, which materially lowers the
stakes of a retrieval bug — and is worth saying, because a RAG service over
sensitive documents has an entirely different threat model that this design
does not address.

## Threat assumptions

**In scope**

- An attacker reaching the HTTP surface and attempting resource exhaustion
- A compromised or buggy release reaching production
- A leaked credential from the repository or CI
- Lateral movement from a compromised application pod
- Data loss through corruption, bad migration or accidental deletion

**Explicitly out of scope**

- **Authentication and authorisation.** `/ask` is unauthenticated. In
  production it would sit behind the platform's existing identity layer; a
  demo that invents its own is less honest than one that says where the real
  boundary is.
- **Multi-tenant isolation.** One corpus, one tenant. Retrieval cannot leak
  documents across tenants because there is only one.
- **Prompt injection.** The corpus is trusted content under our control and
  the model backend is a deterministic stub. With a real model and
  user-supplied documents this becomes the primary risk, and nothing here
  mitigates it.
- **Loss of the cluster.** See the backup section.

## Secrets

Three mechanisms, chosen by who is able to generate the value.

| secret | who generates it | where it lives |
|---|---|---|
| PostgreSQL credentials | CloudNativePG | `jenie-pg-app`, in cluster only |
| SOPS age key | an operator, out of band | Terraform → `flux-system/sops-age` |
| image automation deploy key | GitHub | Terraform → `flux-system` |
| object store credential | an operator, out of band | **SOPS-encrypted in git** |

Nothing is committed in plaintext. `gitleaks` scans the **full history** on
every pull request, not just the diff — a secret removed in a later commit is
still a leaked secret.

The object store credential is the only one encrypted in git, and it has to
be: SeaweedFS and CloudNativePG must agree on one value, so neither can
generate it. `.sops.yaml` holds only the age public key and is committed.

### Known weakness: Terraform state

Terraform writes the age key and the deploy key into the cluster, so
**`terraform.tfstate` contains both private keys in plaintext**. The state
file is exactly as sensitive as the keys themselves.

It is gitignored and local-only here. In production it belongs in an
encrypted remote backend with locking and restricted access, or the keys
should be delivered by something Terraform never sees — an external secrets
operator pulling from a managed vault.

### Known weakness: one key for both environments

dev and prod share a SOPS recipient. One leaked key decrypts both. Separate
keys per environment is a values change, not a design change.

## Least privilege

- Containers run as UID 10001, non-root, read-only root filesystem, **all
  capabilities dropped**, `seccompProfile: RuntimeDefault`
- `automountServiceAccountToken: false` — the application never calls the
  Kubernetes API, so it carries no credential for it
- No RBAC rules are granted to the application service account
- **Default-deny NetworkPolicy**, ingress and egress, with explicit allows:
  in from the gateway, monitoring and the canary load generator; out to
  PostgreSQL and DNS only
- The image-automation deploy key is **repo-scoped**, not a user token. Its
  blast radius is one repository and revoking it breaks only automated tag
  bumps. Reconciliation itself uses public HTTPS with no credential at all.

## Network exposure

The only ingress is the Envoy Gateway on one HTTP listener. Rate limiting is
an Envoy `BackendTrafficPolicy` — 60 requests per minute per proxy — as typed
configuration rather than an annotation string, alongside circuit-breaker
limits that cap in-flight and pending requests.

### Previously false, now true

This document claimed default-deny NetworkPolicy from the start, and in
production it was not in effect. Flagger creates a `<target>-primary`
Deployment with a derived selector label and keeps the original as the
canary, so a policy selecting the original label covered only the canary —
which is scaled to zero at rest. **A NetworkPolicy matching zero pods does
not deny traffic; it does not apply.** The same mistake left the
PodDisruptionBudget and the PodMonitor selecting nothing.

Recorded rather than quietly corrected, because the failure mode is the
point: a security control that selects nothing reports no error, passes
every schema check, and appears in `kubectl get` exactly like one that
works.

### Deliberate: Grafana uses a fixed password

`admin` / `admin`, in plaintext in the HelmRelease. Grafana is reachable
only through `kubectl port-forward` — it is not attached to the Gateway, so
there is no network path to it without cluster credentials, which already
outrank Grafana's own. A generated password rotates on every cluster
rebuild and makes any written instruction wrong.

This does not generalise. Anywhere the console is reachable, it is SSO or a
SOPS-encrypted secret, and the fixed credential is the first thing to
remove.

### Known weakness: health endpoints are public

The HTTPRoute matches `PathPrefix: /`, so `/healthz`, `/readyz` and
`/metrics` are reachable from outside. `/readyz` discloses the indexed chunk
count and `/metrics` discloses request volumes and token spend. The fix is
explicit path rules on the route, or a second listener bound internally.
Not yet done.

### WAF

There is none. The gateway is Envoy, so the natural place for one is an
external processing filter or a WAF in front of the load balancer. The
controls that would matter most for this service are request-size limits on
`/ask` and per-client rate limiting beyond the current per-proxy limit —
local rate limiting does not coordinate across replicas, so the effective
limit is the configured rate multiplied by the replica count.

## Supply chain

- **Trivy** scans every image before it is pushed, with `exit-code: 1` on
  HIGH and CRITICAL. The build fails rather than reporting.
- Images are tagged by commit SHA, so a running container maps to an exact
  commit
- Every Helm chart is **pinned to an exact version**; none float
- The Sloth chart is **vendored** into this repository rather than fetched,
  because it is published only as a GitHub release asset with no mirror —
  one unreachable download was able to leave a cluster with no ingress
- `.terraform.lock.hcl` is committed, pinning provider versions *and*
  checksums

## Data protection

PostgreSQL is not exposed outside the cluster; the only route in is through
the application, and NetworkPolicy restricts even that to the API and indexer
pods. Backups are continuous WAL archiving plus daily base backups.

### Known weakness: the backup target shares a failure domain

The object store runs inside the cluster it backs up. That covers corruption,
a bad migration and accidental deletion — not loss of the cluster. See
[`docs/runbooks/dr-restore.md`](docs/runbooks/dr-restore.md).

## Deployment safety

Production releases are Flagger canaries: traffic shifts 20% at a time with
analysis every 30 seconds, and three failed checks roll back automatically.
One of the three gates is `rag-refusal-rate`, because a release that starts
refusing questions returns HTTP 200 quickly and is invisible to both error
rate and latency.

## Reporting

This is an assessment exercise and not a deployed service. For a real one,
security contact details and a disclosure window belong here.
