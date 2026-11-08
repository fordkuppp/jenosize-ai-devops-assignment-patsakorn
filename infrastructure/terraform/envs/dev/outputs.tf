output "kubeconfig_path" {
  value = module.cluster.kubeconfig_path
}

output "context" {
  value = module.cluster.context_name
}

output "gateway_url" {
  value = "http://localhost:8080"
}
