# Note: The ALB security group is managed in common/alb.tf
# This module only creates the ECS tasks security group

# Security Group for ECS tasks
# Rules are managed externally via aws_security_group_rule resources
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  # Prevent Terraform from fighting with external aws_security_group_rule resources
  lifecycle {
    ignore_changes = [ingress, egress]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}

# Manage ingress rules externally (not inline) to avoid conflicts
resource "aws_security_group_rule" "ecs_from_alb_api" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = var.alb_security_group_id
  security_group_id        = aws_security_group.ecs_tasks.id
  description              = "HTTP from ALB to API"
}

resource "aws_security_group_rule" "ecs_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ecs_tasks.id
  description       = "Allow all outbound traffic"
}
