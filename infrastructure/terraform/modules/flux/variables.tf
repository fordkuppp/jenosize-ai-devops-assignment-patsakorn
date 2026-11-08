variable "git_url" {
  description = "Public HTTPS clone URL. Public on purpose: a reviewer can stand this up with no token, and Flux only needs read access to reconcile."
  type        = string
}

variable "git_branch" {
  type    = string
  default = "main"
}

variable "cluster_path" {
  description = "Path in the repo holding this cluster's root Kustomizations, e.g. ./kubernetes/clusters/dev"
  type        = string
}

variable "chart_version" {
  description = "fluxcd-community/flux2 chart version. Pinned so a cluster rebuild is reproducible."
  type        = string
  default     = "2.20.0"
}

variable "sync_chart_version" {
  type    = string
  default = "1.16.0"
}

variable "sync_interval" {
  type    = string
  default = "1m"
}
