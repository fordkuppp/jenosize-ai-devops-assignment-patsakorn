# Backup and recovery

## What actually needs recovering

Almost nothing. Both clusters are built from the repository: `make up-<env>`
creates the cluster and installs Flux, and Flux reconciles everything else.
The recovery procedure for every stateless component is the command used to
create it.

One component holds state: PostgreSQL. Disaster recovery therefore reduces to
that single question, which is the payoff for keeping everything else
disposable.

## How backups work

CloudNativePG archives WAL continuously and takes a scheduled base backup,
both through the barman-cloud plugin into an S3 bucket. Continuous archiving
is what separates losing seconds from losing up to a day: without it,
recovery can only reach the last base backup.

The plugin is used rather than `spec.backup.barmanObjectStore`, which CNPG
deprecated in 1.26 and has announced for removal. The plugin requires
cert-manager, because it registers with the operator over mTLS.

Base backups run daily at 02:00. The schedule uses a six-field cron — CNPG
uses seconds resolution, so a normal five-field string means something else.

## Restoring

CNPG does not restore into a running cluster. It bootstraps a new Cluster
from the object store using `bootstrap.recovery` and `externalClusters`. The
damaged instance stays untouched for forensics, and cutover is a change to
which service the application targets. Renaming a CNPG cluster is not
supported.

Verify the `vector` extension exists in the restored database before cutting
over — a restored database is the most likely place for it to be missing.

## The gap

The object store runs inside the cluster it backs up. That protects against
data corruption, a bad migration and accidental deletion — not against losing
the cluster. In production the bucket belongs in a different failure domain.
The configuration change is one endpoint URL and a credential, which is why
an S3 API was used rather than volume snapshots.
