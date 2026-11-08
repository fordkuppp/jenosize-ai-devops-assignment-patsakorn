# Stage 2: everything that needs a reachable Kubernetes API.
#
# The cluster is NOT created here, and that split is not stylistic. The
# kubernetes provider validates config_path during *plan*, before any resource
# is applied, so a root module that both creates a cluster and configures a
# provider from its kubeconfig fails before it creates anything:
#
#   Invalid attribute in provider configuration
#   'config_path' refers to an invalid path: .../.kube/config
#
# Configuring the provider from the cluster resource's attributes instead
# would make the provider config depend on a resource inside the same module
# that the provider serves, which is a dependency cycle. Two applies is the
# way out, and it also matches reality: a cluster and what runs on it have
# different lifecycles and different blast radii.

module "secrets" {
  source = "../bootstrap-secrets"

  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts
}

module "flux" {
  source = "../flux"

  git_url      = var.git_url
  git_branch   = var.git_branch
  cluster_path = var.cluster_path
  namespace    = module.secrets.flux_namespace
}
