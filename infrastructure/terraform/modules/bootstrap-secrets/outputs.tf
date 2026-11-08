output "app_namespace" {
  value = kubernetes_namespace.app.metadata[0].name
}

output "image_automation_enabled" {
  value = length(kubernetes_secret.image_automation) > 0
}

output "flux_namespace" {
  value = kubernetes_namespace.flux.metadata[0].name
}
