variable "git_url" {
  type    = string
  default = "https://github.com/fordkuppp/jenosize-ai-devops-assignment-patsakorn.git"
}

variable "git_branch" {
  type    = string
  default = "main"
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
