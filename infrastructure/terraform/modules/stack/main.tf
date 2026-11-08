# One environment, composed.
#
# Both envs wired these three modules identically and differed only in five
# literals. Composing once here makes "dev and prod differ by values, not
# structure" true by construction rather than by discipline: a change to the
# wiring cannot land in one env and miss the other.

module "cluster" {
  source = "../kind-cluster"

  name            = var.cluster_name
  worker_count    = var.worker_count
  kubeconfig_path = var.kubeconfig_path
  port_mappings   = var.port_mappings
}

module "secrets" {
  source = "../bootstrap-secrets"

  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts

  depends_on = [module.cluster]
}

module "flux" {
  source = "../flux"

  git_url      = var.git_url
  git_branch   = var.git_branch
  cluster_path = var.cluster_path

  depends_on = [module.cluster, module.secrets]
}
