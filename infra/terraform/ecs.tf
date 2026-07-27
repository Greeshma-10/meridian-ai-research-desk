resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each          = toset(["chroma", "ingestion-service", "retrieval-service", "agent-orchestrator", "api-gateway"])
  name              = "/ecs/${var.project_name}-${each.value}"
  retention_in_days = 3
}