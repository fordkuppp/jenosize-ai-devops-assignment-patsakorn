# dev — one worker, high host ports so it can run beside prod.
module "stack" {
  source = "../../modules/stack"

  cluster_name    = "jenie-dev"
  worker_count    = 1
  kubeconfig_path = local.kubeconfig
  cluster_path    = "./kubernetes/clusters/dev"

  port_mappings = [
    { container_port = 30080, host_port = 8080 },
    { container_port = 30443, host_port = 8443 },
  ]

  git_url                     = var.git_url
  git_branch                  = var.git_branch
  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts
}
