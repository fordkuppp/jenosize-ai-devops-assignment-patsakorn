# dev — one worker, high host ports so it can coexist with prod.
#
# The only differences from prod are values: node count, host ports, and the
# cluster path Flux reconciles. If dev ever needs a resource prod does not
# have, that belongs in docs/decisions.md, not silently here.

module "cluster" {
  source = "../../modules/kind-cluster"

  name            = "jenie-dev"
  worker_count    = 1
  kubeconfig_path = local.kubeconfig

  port_mappings = [
    { container_port = 30080, host_port = 8080 },
    { container_port = 30443, host_port = 8443 },
  ]
}

module "secrets" {
  source = "../../modules/bootstrap-secrets"

  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts

  depends_on = [module.cluster]
}

module "flux" {
  source = "../../modules/flux"

  git_url      = var.git_url
  git_branch   = var.git_branch
  cluster_path = "./kubernetes/clusters/dev"

  depends_on = [module.cluster, module.secrets]
}
