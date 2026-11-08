locals {
  # Written by stage 1. It exists by the time this stage plans, which is the
  # whole reason the stages are separate.
  kubeconfig = abspath("${path.root}/../1-cluster/.kube/config")
}

provider "helm" {
  kubernetes = {
    config_path = local.kubeconfig
  }
}

provider "kubernetes" {
  config_path = local.kubeconfig
}
