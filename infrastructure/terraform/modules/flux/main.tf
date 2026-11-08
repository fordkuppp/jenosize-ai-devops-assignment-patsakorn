# Flux is installed by Helm and pointed at the repo with a plain GitRepository,
# rather than by `flux bootstrap`.
#
# bootstrap needs a PAT with write access and commits the controller manifests
# back into the repo. That makes the repo unreproducible for anyone but the
# owner: a reviewer cannot run it. Installing the controllers as a release and
# declaring the sync separately gives the same end state, read-only, with no
# credential at all.
resource "helm_release" "flux" {
  name = "flux2"
  # OCI rather than the HTTP repo. The HTTP index points at GitHub release
  # assets, which are unreachable from some networks (observed: a proxy
  # returning 504 for github.com/*/releases/download/*). OCI is also the
  # better default regardless: immutable digests, no index to go stale.
  repository = "oci://ghcr.io/fluxcd-community/charts"
  chart      = "flux2"
  version    = var.chart_version
  namespace  = var.namespace
  # false: bootstrap-secrets created it, because the decryption key has to be
  # in place before the controllers start reconciling.
  create_namespace = false

  # Terraform's job ends when the controllers are up. Everything after this
  # point is Flux's, and waiting on it here would make `terraform apply` block
  # on application health — which is the controller's concern, not the
  # provisioner's.
  wait    = true
  timeout = 600
}

resource "helm_release" "sync" {
  name       = "flux2-sync"
  repository = "oci://ghcr.io/fluxcd-community/charts"
  chart      = "flux2-sync"
  version    = var.sync_chart_version
  namespace  = var.namespace

  depends_on = [helm_release.flux]

  values = [yamlencode({
    gitRepository = {
      spec = {
        url      = var.git_url
        interval = var.sync_interval
        ref      = { branch = var.git_branch }
      }
    }
    kustomization = {
      spec = {
        path     = var.cluster_path
        interval = "5m"
        prune    = true
      }
    }
  })]
}
