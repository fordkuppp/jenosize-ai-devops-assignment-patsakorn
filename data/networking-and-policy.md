# Networking and policy

## NetworkPolicy

Every workload runs under a default-deny policy for both ingress and egress,
with explicit allows. Pods are selected by label rather than by workload
name, so the policy covers the `-primary` and `-canary` pods Flagger creates
without naming them.

Ingress is allowed from the gateway namespace and from monitoring. Egress is
allowed to PostgreSQL on 5432, and to kube-dns.

DNS is the one to remember. Without an explicit allow for port 53 to
`kube-dns`, a default-deny egress policy breaks name resolution before it
breaks anything you intended to block, and every subsequent failure looks
like a resolution error rather than a policy one.

## Pod hardening

Containers run as UID 10001, non-root, with a read-only root filesystem, all
capabilities dropped and the `RuntimeDefault` seccomp profile. A read-only
root filesystem means writable paths have to be declared — `/tmp` is an
emptyDir.

Service account tokens are not automounted. The application does not talk to
the Kubernetes API, so it has no reason to carry a credential for it.

## Graceful shutdown

A `preStop` hook sleeps 5 seconds before the process is signalled, giving the
gateway time to stop routing to the pod. Without it every rollout drops
in-flight requests, which shows up as error-budget burn during a deploy that
otherwise looks clean.

## Probes

Liveness checks only that the process is alive. Readiness checks the database
and that the index is populated. The split is deliberate: a liveness probe
with a dependency check turns one database blip into a simultaneous restart
of every replica, while readiness removes a pod from the load balancer and
leaves it running.
