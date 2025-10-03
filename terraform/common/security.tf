# Security Groups
resource "aws_security_group" "rds" {
  name        = "fastapi-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id

  # MySQL access from ECS tasks (will be added by environment-specific configs)
  ingress {
    description = "MySQL from ECS tasks"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # MySQL access from bastion host
  ingress {
    description     = "MySQL from bastion host"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # MySQL access from webserver
  ingress {
    description     = "MySQL from webserver"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.webserver.id]
  }

  # MySQL access from phpMyAdmin ECS tasks
  ingress {
    description     = "MySQL from phpMyAdmin ECS tasks"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.phpmyadmin_ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fastapi-rds-sg"
  }

  # Ignore changes to ingress rules managed separately
  lifecycle {
    ignore_changes = [ingress]
  }
}
