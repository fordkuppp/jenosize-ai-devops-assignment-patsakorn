locals {
  # Static path, not a resource attribute. A provider configured from an
  # unknown value fails at plan time; this is the standard way out of the
  # "create a cluster and install into it in one apply" problem.
  kubeconfig = abspath("${path.root}/.kube/config")
}

provider "kind" {}

provider "helm" {
  kubernetes = {
    config_path = local.kubeconfig
  }
}

provider "kubernetes" {
  config_path = local.kubeconfig
}
