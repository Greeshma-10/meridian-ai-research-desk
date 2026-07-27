# Declares which "provider" (cloud vendor plugin) Terraform should use,
# and pins its version so a future provider update can't silently change
# behavior under you — same philosophy as pinning package versions in
# requirements.txt.
terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}