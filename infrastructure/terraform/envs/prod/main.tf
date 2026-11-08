# prod — two workers so PodDisruptionBudgets and topology spread mean
# something, and the conventional ports.

module "cluster" {
  source = "../../modules/kind-cluster"

  name            = "jenie-prod"
  worker_count    = 2
  kubeconfig_path = local.kubeconfig

  port_mappings = [
    { container_port = 30080, host_port = 80 },
    { container_port = 30443, host_port = 443 },
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
  cluster_path = "./kubernetes/clusters/prod"

  depends_on = [module.cluster, module.secrets]
}
