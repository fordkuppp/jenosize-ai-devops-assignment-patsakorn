locals {
  # One dynamic block over a computed list rather than a static control-plane
  # block plus a dynamic worker block: node ordering matters to kind, and
  # mixing static and dynamic blocks of the same name makes it implicit.
  nodes = concat(
    [{ role = "control-plane", ports = var.port_mappings }],
    [for i in range(var.worker_count) : { role = "worker", ports = [] }]
  )
}

resource "kind_cluster" "this" {
  name            = var.name
  node_image      = var.node_image
  kubeconfig_path = var.kubeconfig_path
  wait_for_ready  = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    dynamic "node" {
      for_each = local.nodes
      content {
        role = node.value.role

        dynamic "extra_port_mappings" {
          for_each = node.value.ports
          content {
            container_port = extra_port_mappings.value.container_port
            host_port      = extra_port_mappings.value.host_port
            protocol       = "TCP"
          }
        }
      }
    }
  }
}
