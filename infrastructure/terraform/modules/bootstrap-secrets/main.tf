# The only secrets Terraform seeds are the ones Flux cannot source from git:
# the key that decrypts everything else, and the key that lets Flux write back.
#
# Everything else — database credentials in particular — is generated in
# cluster by the operator that owns it. CloudNativePG creates its own
# `<cluster>-app` secret; duplicating that here would mean two sources of
# truth for one password.

resource "kubernetes_namespace" "app" {
  metadata {
    name = var.app_namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      # Consumed by NetworkPolicy peers in other namespaces.
      "kubernetes.io/metadata.name" = var.app_namespace
    }
  }
}

# Flux Kustomizations reference this by name in spec.decryption.secretRef.
resource "kubernetes_secret" "sops_age" {
  metadata {
    name      = "sops-age"
    namespace = "flux-system"
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
    namespace = "flux-system"
  }
  data = {
    identity      = var.image_automation_deploy_key
    "known_hosts" = var.git_known_hosts
  }
  type = "Opaque"
}
