variable "name" {
  description = "Cluster name. Becomes the kubectl context as kind-<name>."
  type        = string
}

variable "node_image" {
  description = "kindest/node image. Pinned, not latest: the Kubernetes version is part of the environment definition."
  type        = string
  default     = "kindest/node:v1.35.0"
}

variable "worker_count" {
  description = "Worker nodes in addition to the control plane."
  type        = number
  default     = 1
}

variable "kubeconfig_path" {
  description = <<-EOT
    Where to write the kubeconfig. Deliberately a static path rather than a
    resource attribute: the helm and kubernetes providers are configured from
    it, and a provider configured from an unknown value fails at plan time.
  EOT
  type        = string
}

variable "port_mappings" {
  description = "Host ports forwarded to the control-plane node. Two clusters cannot share a host port, which is why dev and prod differ here."
  type = list(object({
    container_port = number
    host_port      = number
  }))
  default = []
}
