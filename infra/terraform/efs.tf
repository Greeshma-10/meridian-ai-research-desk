resource "aws_efs_file_system" "chroma_data" {
  tags = { Name = "${var.project_name}-chroma-data" }
}

resource "aws_efs_mount_target" "chroma_data" {
  count           = 2
  file_system_id  = aws_efs_file_system.chroma_data.id
  subnet_id       = aws_subnet.public[count.index].id
  security_groups = [aws_security_group.ecs_tasks.id]
}