variable "app_namespace" {
  type    = string
  default = "jenie"
}

variable "sops_age_key" {
  description = <<-EOT
    The age private key Flux uses to decrypt SOPS-encrypted manifests.

    Supplied from outside, never generated here. Terraform state stores values
    in plaintext, so generating a root decryption key inside Terraform would
    make the state file equivalent to the key itself — and state is the one
    artifact people copy around casually. Generate it with `age-keygen`, keep
    it in a password manager, pass it as TF_VAR_sops_age_key.
  EOT
  type        = string
  sensitive   = true
}

variable "image_automation_deploy_key" {
  description = <<-EOT
    SSH private key for the repo deploy key Flux image-automation commits with.
    The only write credential in the system. Optional: leave empty and image
    automation is simply not bootstrapped.
  EOT
  type        = string
  sensitive   = true
  default     = ""
}

variable "git_known_hosts" {
  description = "Output of `ssh-keyscan github.com`. Pinned rather than trusted on first use."
  type        = string
  default     = ""
}
