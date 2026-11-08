# Runbook — disaster recovery

## What actually needs recovering

Almost nothing. Both clusters are built from this repository: `make up-<env>`
creates the cluster and installs Flux, and Flux reconciles everything else.
That path has been exercised repeatedly, including full teardown and rebuild,
so the recovery procedure for every stateless component is "run the same
command you used to create it."

**One component holds state: PostgreSQL.** Disaster recovery therefore reduces
to that single question, which is the point of keeping everything else
disposable.

| | RPO | RTO | mechanism |
|---|---|---|---|
| cluster, controllers, gateway, policy | 0 — it is in git | ~3 min | `make up-<env>`, then Flux |
| application config, SLOs, alerts | 0 — it is in git | included above | Flux |
| **database** | **seconds** (WAL archiving) | ~5 min | CNPG + barman-cloud |
| object store itself | — | — | see "the honest gap" |

## Database recovery

CloudNativePG archives WAL continuously and takes a scheduled base backup, both
through the barman-cloud plugin into the S3 bucket. Continuous archiving is what
separates "lose up to a day" from "lose a few seconds": without it, recovery can
only reach the last base backup.

### Check the backups are real before you need them

```sh
make status ENV=prod
kubectl -n jenie get backups.postgresql.cnpg.io
kubectl -n jenie get objectstore jenie-backups -o yaml | yq '.status'
```

An alert exists for staleness — but a backup that has never been *restored* is
a hypothesis, not a backup. Run the drill below on a schedule.

### Restore to a point in time

CNPG does not restore into the running cluster. It bootstraps a **new** Cluster
from the object store, which is safer: the damaged instance stays untouched and
available for forensics until you choose to cut over.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: jenie-pg-restored
  namespace: jenie
spec:
  instances: 1
  imageName: ghcr.io/fordkuppp/postgres-pgvector:17
  storage:
    size: 2Gi
  bootstrap:
    recovery:
      source: jenie-backups
      # Omit to recover to the latest available WAL.
      recoveryTarget:
        targetTime: "2026-11-08 12:00:00+00"
  externalClusters:
    - name: jenie-backups
      plugin:
        name: barman-cloud.cloudnative-pg.io
        parameters:
          barmanObjectName: jenie-backups
```

```sh
kubectl apply -f /tmp/restore.yaml
kubectl -n jenie get cluster jenie-pg-restored -w

# verify before cutting over — including the extension, which is the thing
# most likely to be missing in a restored database
kubectl -n jenie exec jenie-pg-restored-1 -c postgres -- \
  psql -U postgres -d jenie -c "select extname from pg_extension;"
kubectl -n jenie exec jenie-pg-restored-1 -c postgres -- \
  psql -U postgres -d jenie -c "select count(*) from information_schema.tables;"
```

Cut over by pointing the application at `jenie-pg-restored-rw`, not by renaming
anything. Renaming a CNPG cluster is not a supported operation.

## The honest gap

The object store runs **inside the cluster it backs up**. Losing the cluster
loses both the database and its backups, which means this protects against
data corruption, a bad migration and accidental deletion — not against losing
the cluster.

That is acceptable for a disposable kind environment and is not acceptable in
production, where the bucket belongs in a different failure domain: a managed
object store in another region, or at minimum a different cluster. The
configuration does not change — only `endpointURL` and the credential — which
is the reason for using an S3 API rather than a volume snapshot.

## Drill

Quarterly, and after any change to the backup configuration:

1. restore to a timestamp from the middle of the retention window
2. confirm row counts and `pg_extension` match expectations
3. record how long it took — RTO is a measurement, not an aspiration
4. delete the restored cluster
