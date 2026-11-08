output "kubeconfig_path" {
  value = module.cluster.kubeconfig_path
}

output "context" {
  value = module.cluster.context_name
}
