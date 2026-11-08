output "name" {
  value = kind_cluster.this.name
}

output "context_name" {
  value = kind_cluster.this.context_name
}

output "kubeconfig_path" {
  value = var.kubeconfig_path
}

output "endpoint" {
  value = kind_cluster.this.endpoint
}
