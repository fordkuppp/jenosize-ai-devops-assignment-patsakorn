# Deploying a service

## The flow

Commit to `main`. Flux pulls within a minute, applies the manifests, and
Flagger promotes the new version in production after analysis passes.

Nothing is deployed with `kubectl`. After bootstrap, `kubectl apply` is a
debugging tool, not a deployment tool — anything applied by hand is reverted
on the next reconciliation, which is the drift GitOps exists to eliminate.

To make a change take effect immediately rather than waiting out the sync
interval, use `make reconcile`.

## Image tags

Image automation watches the registry, selects the newest tag matching the
policy's semver range, and commits the new tag back to the repository. The
deployment follows from that commit like any other change, so the running
version is always derivable from git history.

This is the only write credential in the system. Reconciliation reads over
public HTTPS with no credential at all; only the automation path needs a key,
and it is a repo-scoped deploy key rather than a user token — its blast
radius is one repository and revoking it breaks nothing but automated tag
bumps.

## The service-policy chart

Routing, rate limiting, progressive delivery, network policy, autoscaling and
monitoring wiring come from one chart. It owns no workload: the Deployment
and Service are plain manifests, and the chart takes a reference to them.

The chart's job is the policy layer, because the pod layer already has good
tooling and rebuilding it adds nothing.

## Adding a second service

Attach an HTTPRoute to the existing `Gateway/external`, add a release of the
policy chart pointing at the new workload, and declare its SLOs as a
`PrometheusServiceLevel`. No change is needed under `infrastructure/`.
