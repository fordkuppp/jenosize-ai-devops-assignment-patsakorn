# Vendored: sloth 0.16.0

Upstream: https://github.com/slok/sloth
Source:   `deploy/kubernetes/helm/sloth/` at tag `sloth-helm-chart-0.16.0`
Vendored: 2026-11-08 — unmodified

## Why

Sloth publishes its chart only as a GitHub **release asset**, and release
assets are unreachable from some networks — we observed a proxy returning
`504 Gateway Time-out` for `github.com/*/releases/download/*`, intermittently,
on both the host and from inside the cluster. Unlike every other chart here,
sloth has no OCI mirror to fall back to.

That turned one flaky third-party download into a cluster-wide outage: the
`infra-controllers` Kustomization uses `wait: true`, so a HelmRelease that
cannot pull its chart blocks `infra-configs` and `apps` behind it. A rebuild
of the dev cluster came up with no gateway and no application because Sloth's
tarball happened to 504 that minute.

Vendoring removes the fetch. The chart is now reconciled from this repo, the
same GitRepository Flux already reads, so installing it cannot fail for a
reason outside the cluster.

## Updating

```sh
# fetch a newer tag's chart directory from source, not from a release asset
REF=sloth-helm-chart-<version>
# see the fetch loop in the commit that introduced this file
```

Then bump `version` in the HelmRelease comment and diff before committing —
vendoring means upstream fixes arrive only when someone pulls them.
