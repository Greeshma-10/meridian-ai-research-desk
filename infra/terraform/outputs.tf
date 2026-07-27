# Outputs are how Terraform surfaces useful info after apply completes —
# here, the actual ECR repo URLs we'll need later to push images to.

output "ecr_repository_urls" {
  description = "ECR repository URLs, one per service"
  value       = { for k, v in aws_ecr_repository.service : k => v.repository_url }
}