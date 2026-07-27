locals {
  account_id = "162026158786"
  ecr_base   = "${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

resource "aws_ecs_task_definition" "chroma" {
  family                   = "${var.project_name}-chroma"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  volume {
    name = "chroma-storage"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.chroma_data.id
    }
  }

  container_definitions = jsonencode([{
    name         = "chroma"
    image        = "chromadb/chroma:0.5.20"
    portMappings = [{ containerPort = 8000 }]
    environment  = [{ name = "IS_PERSISTENT", value = "TRUE" }]
    mountPoints  = [{ sourceVolume = "chroma-storage", containerPath = "/chroma/chroma" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}-chroma"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "chroma"
      }
    }
  }])
}

resource "aws_ecs_service" "chroma" {
  name            = "chroma"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.chroma.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.service["chroma"].arn
  }
}

resource "aws_ecs_task_definition" "retrieval" {
  family                   = "${var.project_name}-retrieval-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "3072"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name         = "retrieval-service"
    image        = "${local.ecr_base}/meridian-retrieval-service:latest"
    portMappings = [{ containerPort = 8001 }]
    environment  = [{ name = "CHROMA_HOST", value = "chroma.meridian.local" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}-retrieval-service"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "retrieval"
      }
    }
  }])
}

resource "aws_ecs_service" "retrieval" {
  name            = "retrieval-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.retrieval.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_ecs_service.chroma]

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.service["retrieval-service"].arn
  }
}

resource "aws_ecs_task_definition" "ingestion" {
  family                   = "${var.project_name}-ingestion-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name         = "ingestion-service"
    image        = "${local.ecr_base}/meridian-ingestion-service:latest"
    portMappings = [{ containerPort = 8002 }]
    environment = [
      { name = "CHROMA_HOST", value = "chroma.meridian.local" },
      { name = "RETRIEVAL_SERVICE_URL", value = "http://retrieval-service.meridian.local:8001" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}-ingestion-service"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ingestion"
      }
    }
  }])
}

resource "aws_ecs_service" "ingestion" {
  name            = "ingestion-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ingestion.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_ecs_service.retrieval]

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.service["ingestion-service"].arn
  }
}

resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "${var.project_name}-agent-orchestrator"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name         = "agent-orchestrator"
    image        = "${local.ecr_base}/meridian-agent-orchestrator:latest"
    portMappings = [{ containerPort = 8003 }]
    environment = [
      { name = "INGESTION_SERVICE_URL", value = "http://ingestion-service.meridian.local:8002" },
      { name = "RETRIEVAL_SERVICE_URL", value = "http://retrieval-service.meridian.local:8001" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}-agent-orchestrator"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "orchestrator"
      }
    }
  }])
}

resource "aws_ecs_service" "orchestrator" {
  name            = "agent-orchestrator"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_ecs_service.ingestion]

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.service["agent-orchestrator"].arn
  }
}

resource "aws_ecs_task_definition" "gateway" {
  family                   = "${var.project_name}-api-gateway"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn             = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name         = "api-gateway"
    image        = "${local.ecr_base}/meridian-api-gateway:latest"
    portMappings = [{ containerPort = 8080 }]
    environment  = [{ name = "AGENT_ORCHESTRATOR_URL", value = "http://agent-orchestrator.meridian.local:8003" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}-api-gateway"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "gateway"
      }
    }
  }])
}

resource "aws_ecs_service" "gateway" {
  name            = "api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_ecs_service.orchestrator]

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.gateway.arn
    container_name    = "api-gateway"
    container_port    = 8080
  }
}