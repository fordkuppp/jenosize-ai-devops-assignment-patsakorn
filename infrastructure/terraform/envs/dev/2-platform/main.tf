# Stage 2 — secrets Flux cannot source from git, then Flux itself.
module "platform" {
  source = "../../../modules/platform"

  cluster_path = "./kubernetes/clusters/dev"

  git_url                     = var.git_url
  git_branch                  = var.git_branch
  sops_age_key                = var.sops_age_key
  image_automation_deploy_key = var.image_automation_deploy_key
  git_known_hosts             = var.git_known_hosts
}
