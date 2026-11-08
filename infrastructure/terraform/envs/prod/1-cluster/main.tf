# Stage 1 — the cluster and nothing else.
#
# No kubernetes or helm provider is configured here, which is the point: this
# stage must be able to plan against a world where the cluster does not exist.

provider "kind" {}

locals {
  # Stage 2 reads this same path. Keeping it next to stage 1's state means
  # destroying the cluster and its kubeconfig are one operation.
  kubeconfig = abspath("${path.root}/.kube/config")
}

module "cluster" {
  source = "../../../modules/kind-cluster"

  name            = "jenie-prod"
  worker_count    = 2
  kubeconfig_path = local.kubeconfig

  port_mappings = [
    { container_port = 30080, host_port = 80 },
    { container_port = 30443, host_port = 443 },
  ]
}
