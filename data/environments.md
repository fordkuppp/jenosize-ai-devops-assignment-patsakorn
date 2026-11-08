# Environments

There are two clusters, `jenie-dev` and `jenie-prod`. They run the same
manifests and differ only in values.

## Differences

| | dev | prod |
|---|---|---|
| worker nodes | 1 | 2 |
| host ports | 8080 / 8443 | 80 / 443 |
| deployment strategy | RollingUpdate | Canary |
| autoscaling | off | on, 2 to 6 replicas |
| PodDisruptionBudget | off | on |
| PostgreSQL instances | 1 | 3 |
| backup retention | 7 days | 30 days |
| apps reconcile timeout | 5 minutes | 15 minutes |

## Why the timeouts differ

With `wait: true`, Flux will not begin a new reconciliation until the current
one finishes. The timeout is therefore not only how long a broken apply is
tolerated — it is how long a fix in git stays unreachable.

dev uses RollingUpdate, so a healthy apply completes in seconds and anything
longer means something is stuck: 5 minutes. prod runs a Flagger canary whose
analysis legitimately takes minutes, and aborting it would fail healthy
rollouts: 15 minutes, accepting the slower path back from a bad apply.

## Creating and destroying

    make up-dev          create the cluster and bootstrap Flux
    make down-dev        destroy it
    make status ENV=prod what Flux thinks of the world
    make reconcile       pull from git now rather than waiting

Teardown drops the platform stage's Terraform state rather than destroying it
resource by resource. Nothing stage 2 creates outlives the cluster, so
uninstalling Helm releases first is wasted work — and Flux's CRD finalizers
make that uninstall hang for minutes.
