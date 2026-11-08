# The only secrets Terraform seeds are the ones Flux cannot source from git:
# the key that decrypts everything else, and the key that lets Flux write back.
#
# Nothing application-shaped belongs here. Database credentials are generated
# in cluster by CloudNativePG as `<cluster>-app`, and the application namespace
# is declared in kubernetes/apps — a platform bootstrap that knows an
# application's name is a layering error, the same one that put a tenant name
# on a GatewayClass.

# Terraform seeds secrets into flux-system before Flux is installed, so it has
# to own the namespace too. Letting the Helm release create it is a trap: the
# secrets module runs first by design — Flux must find its decryption key
# already present rather than reconcile, fail, and retry.
resource "kubernetes_namespace" "flux" {
  metadata {
    name = "flux-system"
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "kubernetes.io/metadata.name"  = "flux-system"
      # Flux's own kustomize-controller applies this label; setting it here
      # keeps the namespace from flapping between managers.
      "app.kubernetes.io/part-of" = "flux"
    }
  }
}

# Flux Kustomizations reference this by name in spec.decryption.secretRef.
resource "kubernetes_secret" "sops_age" {
  metadata {
    name      = "sops-age"
    namespace = kubernetes_namespace.flux.metadata[0].name
  }
  data = {
    "age.agekey" = var.sops_age_key
  }
  type = "Opaque"
}

resource "kubernetes_secret" "image_automation" {
  count = var.image_automation_deploy_key != "" ? 1 : 0

  metadata {
    name      = "flux-image-automation"
    namespace = kubernetes_namespace.flux.metadata[0].name
  }
  data = {
    identity      = var.image_automation_deploy_key
    "known_hosts" = var.git_known_hosts
  }
  type = "Opaque"
}
