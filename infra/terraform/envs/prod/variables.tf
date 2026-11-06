variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

# Set to a Floci endpoint locally and in CI; leave empty to target real AWS.
# This single variable is the only difference between the two, which is what
# makes the emulator useful as a validation target rather than a toy.
variable "aws_endpoint_url" {
  type    = string
  default = ""
}

variable "environment" {
  type    = string
  default = "prod"
}
