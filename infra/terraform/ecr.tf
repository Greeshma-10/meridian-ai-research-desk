# One ECR repository per microservice — each service's Docker images
# get their own isolated repo, matching our microservice boundaries
# (same reasoning as Milestone 8b: independent things get independent
# infrastructure, not shared/bundled).

locals {
  services = ["ingestion-service", "retrieval-service", "agent-orchestrator", "api-gateway"]
}

resource "aws_ecr_repository" "service" {
  for_each = toset(local.services)

  name                 = "${var.project_name}-${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true  # Free vulnerability scanning on every image push — good security default, zero extra cost
  }

  tags = {
    Project = var.project_name
    Service = each.value
  }
}