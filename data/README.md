# Knowledge base

The corpus Jenie answers from: operations documentation for the platform it
runs on. Self-referential on purpose — a help desk is most useful when it
knows the system the person asking is already using, and every statement here
is verifiable against the repository.

## Contents

| document | covers |
|---|---|
| `platform-overview.md` | layers, controllers, why not Ingress |
| `environments.md` | dev and prod differences, make targets |
| `gateway-and-routing.md` | Gateway API, NodePort, rate limiting |
| `progressive-delivery.md` | canary analysis, gates, rollback |
| `observability.md` | metrics, PodMonitor, histogram buckets |
| `slos-and-alerting.md` | objectives, burn rate, non-SLO alerts |
| `database.md` | CloudNativePG, pgvector, schema |
| `backup-and-recovery.md` | WAL archiving, restore, the gap |
| `secrets.md` | three mechanisms and who generates what |
| `networking-and-policy.md` | NetworkPolicy, hardening, probes |
| `deploying-a-service.md` | the deploy flow, image automation |
| `troubleshooting.md` | symptoms seen in practice |

Headings become citation titles, so documents with a clear heading structure
retrieve better than one long wall of text.
