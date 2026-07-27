# Variables let the same Terraform code be reused across environments
# (dev/staging/prod) by just changing values, not the code itself —
# same principle as our pydantic Settings classes from earlier milestones.

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Used as a prefix for naming all resources, so they're identifiable and won't collide with anything else in the account"
  type        = string
  default     = "meridian"
}