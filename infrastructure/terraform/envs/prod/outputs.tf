output "kubeconfig_path" {
  value = module.stack.kubeconfig_path
}

output "context" {
  value = module.stack.context
}

output "gateway_url" {
  value = "http://localhost"
}
