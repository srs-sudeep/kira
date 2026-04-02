terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    # Values supplied via -backend-config or partial config file.
    # Run: terraform init \
    #   -backend-config="bucket=<your-state-bucket>" \
    #   -backend-config="key=kira/production/terraform.tfstate" \
    #   -backend-config="region=ap-south-1" \
    #   -backend-config="dynamodb_table=kira-terraform-locks" \
    #   -backend-config="encrypt=true"
    #
    # Or fill in the values below for a fully-configured backend (do not commit
    # real bucket names if this repo is public):
    bucket         = "REPLACE_WITH_STATE_BUCKET"
    key            = "kira/production/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "kira-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

# ---------------------------------------------------------------------------
# Locals
# ---------------------------------------------------------------------------

locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Services that get ECR repositories and Secrets Manager entries
  services = [
    "identity-service",
    "rate-inventory-service",
    "reservation-service",
    "channel-engine",
    "notification-service",
    "admin-service",
    "web-app",
  ]
}
