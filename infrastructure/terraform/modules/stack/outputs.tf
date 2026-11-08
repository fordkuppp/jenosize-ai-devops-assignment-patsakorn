output "context" {
  value = module.cluster.context_name
}

output "kubeconfig_path" {
  value = module.cluster.kubeconfig_path
}
