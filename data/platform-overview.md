# Platform overview

Jenie runs on Kubernetes. Terraform creates the cluster and installs Flux;
everything after that is reconciled from git. Nothing is applied by hand.

## Layers

**Terraform** owns only what Flux cannot source from git: the cluster itself,
the SOPS age key used to decrypt secrets, and the deploy key image automation
commits with. Two stages — `1-cluster` then `2-platform` — because the
Kubernetes provider validates its kubeconfig during plan, before any resource
exists.

**Flux** reconciles three Kustomizations in a dependency chain:
`infra-controllers`, then `infra-configs`, then `apps`. The order matters:
controllers install CRDs, configs are custom resources of those CRDs, and the
application depends on both.

## Controllers

| controller | purpose |
|---|---|
| Envoy Gateway | north-south traffic via Gateway API |
| CloudNativePG | PostgreSQL lifecycle, failover, backups |
| Flagger | progressive delivery and automatic rollback |
| Sloth | generates burn-rate alerts from SLO definitions |
| kube-prometheus-stack | metrics, alerting, dashboards |
| cert-manager | certificates for the backup plugin's mTLS |
| barman-cloud plugin | WAL archiving and base backups |

## Why not Ingress

Ingress NGINX was retired by Kubernetes SIG Network in March 2026, and its
intended replacement InGate was retired alongside it. Routing uses Gateway
API, implemented by Envoy Gateway.
