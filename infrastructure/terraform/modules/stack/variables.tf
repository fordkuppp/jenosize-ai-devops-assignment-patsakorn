variable "cluster_name" { type = string }
variable "kubeconfig_path" { type = string }

variable "worker_count" {
  type    = number
  default = 1
}

variable "port_mappings" {
  type = list(object({
    container_port = number
    host_port      = number
  }))
}

variable "git_url" { type = string }

variable "git_branch" {
  type    = string
  default = "main"
}

variable "cluster_path" {
  description = "Repo path holding this cluster's root Kustomizations."
  type        = string
}

variable "sops_age_key" {
  type      = string
  sensitive = true
}

variable "image_automation_deploy_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "git_known_hosts" {
  type    = string
  default = ""
}
