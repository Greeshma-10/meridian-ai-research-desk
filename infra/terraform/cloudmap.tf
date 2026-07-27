resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "meridian.local"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "service" {
  for_each = toset(["chroma", "retrieval-service", "ingestion-service", "agent-orchestrator"])
  name     = each.value

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}