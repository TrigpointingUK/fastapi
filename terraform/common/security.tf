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

# ## SSM interface endpoints removed (cost); ECS Exec will use NAT egress
# ## Re-introduce Interface Endpoints for ECS Exec reliability

# resource "aws_security_group" "vpc_endpoints" {
#   name        = "${var.project_name}-vpc-endpoints-sg"
#   description = "SG for VPC Interface Endpoints (SSM/EC2Messages/SSMMessages)"
#   vpc_id      = aws_vpc.main.id

#   # Allow HTTPS from ECS tasks SG
#   ingress {
#     from_port       = 443
#     to_port         = 443
#     protocol        = "tcp"
#     security_groups = [aws_security_group.phpbb_ecs.id]
#     description     = "HTTPS from phpBB ECS tasks"
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

# Security group for Valkey ECS service
resource "aws_security_group" "valkey_ecs" {
  name        = "${var.project_name}-valkey-ecs-sg"
  description = "Security group for Valkey ECS service"
  vpc_id      = aws_vpc.main.id

  # Valkey port from ECS tasks
  ingress {
    description     = "Valkey from MediaWiki ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.mediawiki_ecs.id]
  }

  ingress {
    description = "Valkey from FastAPI ECS tasks"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr] # Will be restricted by environment-specific rules
  }

  ingress {
    description     = "Valkey from phpBB ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.phpbb_ecs.id]
  }

  ingress {
    description     = "Valkey from bastion (for maintenance)"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # Redis Commander port from ALB
  ingress {
    description     = "Redis Commander from ALB"
    from_port       = 8081
    to_port         = 8081
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-valkey-ecs-sg"
  }
}
