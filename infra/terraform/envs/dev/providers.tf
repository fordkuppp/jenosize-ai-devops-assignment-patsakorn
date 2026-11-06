locals {
  emulated = var.aws_endpoint_url != ""

  tags = {
    Project     = "jenie-helpdesk-ai"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

provider "aws" {
  region = var.aws_region

  access_key                  = local.emulated ? "test" : null
  secret_key                  = local.emulated ? "test" : null
  skip_credentials_validation = local.emulated
  skip_metadata_api_check     = local.emulated
  skip_requesting_account_id  = local.emulated

  default_tags {
    tags = local.tags
  }

  dynamic "endpoints" {
    for_each = local.emulated ? [1] : []
    content {
      cloudwatch     = var.aws_endpoint_url
      ec2            = var.aws_endpoint_url
      ecr            = var.aws_endpoint_url
      ecs            = var.aws_endpoint_url
      elbv2          = var.aws_endpoint_url
      iam            = var.aws_endpoint_url
      logs           = var.aws_endpoint_url
      rds            = var.aws_endpoint_url
      s3             = var.aws_endpoint_url
      secretsmanager = var.aws_endpoint_url
      sts            = var.aws_endpoint_url
    }
  }
}
