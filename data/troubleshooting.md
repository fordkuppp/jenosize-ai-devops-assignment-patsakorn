# Troubleshooting

## A Kustomization is stuck "Reconciliation in progress"

With `wait: true`, Flux will not start a new reconciliation until the current
one finishes, and an in-flight reconcile keeps the timeout it started with —
changing `spec.timeout` does not rescue it. `flux suspend` only blocks new
reconciliations, so it does not abort one either. Wait it out, or for a
disposable cluster, rebuild.

Check `lastAppliedRevision`: if it is empty while the GitRepository artifact
has advanced, the revision in git has never been applied.

## "no matches for kind X"

The CRD is not installed, or the apiVersion does not exist. Controllers must
be Ready before their custom resources apply, which is what the `dependsOn`
chain between Kustomizations is for.

`kustomize build` cannot catch this because it does not know what the cluster
serves, and a schema check passes against a catalogue that may still carry a
removed version. `make verify ENV=<env>` server-side dry-runs every overlay
against the live API server, which is the only check that will.

## The gateway returns 404 or 503

404 means Envoy is listening but no HTTPRoute matched. 503 means a route
matched and has no healthy backend — check pod readiness.

A connection timeout rather than either of those is usually
`externalTrafficPolicy`: see the gateway document.

## A pod is CrashLoopBackOff with no logs

`StartError` with exit code 128 means the container never started. Check the
events: `exec: "--flag": executable file not found` means `args` were set
without `command` on an image that declares `CMD` and no `ENTRYPOINT` — in
Kubernetes `args` replaces `CMD`, so with nothing to prepend them to the args
become the command.

## /ask returns a refusal for a question the docs cover

Retrieval found nothing above `RETRIEVAL_MIN_SIMILARITY`. Check
`rag_retrieval_score` — if the distribution has shifted, the index changed.
Confirm `rag_index_documents` is non-zero and the indexer ran recently.

## An SLO reports healthy but you do not believe it

Check that the threshold is an actual histogram bucket boundary. A query for
a boundary that does not exist matches no series, and the objective reports
healthy because it is measuring nothing.
