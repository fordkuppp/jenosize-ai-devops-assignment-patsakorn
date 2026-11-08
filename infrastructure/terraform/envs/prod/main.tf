# prod — two workers, so PodDisruptionBudgets and topology spread mean
# something rather than being decoration.
module "stack" {
  source = "../../modules/stack"

  cluster_name    = "jenie-prod"
  worker_count    = 2
  kubeconfig_path = local.kubeconfig
  cluster_path    = "./kubernetes/clusters/prod"

  port_mappings = [
    { container_port = 30080, host_port = 80 },
    { container_port = 30443, host_port = 443 },
  ]

  git_url                     = var.git_url
  git_branch                  = var.git_branch
  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts
}
