# Security Groups
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
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
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from ECS tasks"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  # Note: Admin access via bastion host - see bastion.tf
  # Note: DMS access via separate security group rules below

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

# Security group for DMS replication instances
resource "aws_security_group" "dms" {
  count = var.enable_dms_access ? 1 : 0

  name        = "${var.project_name}-${var.environment}-dms-sg"
  description = "Security group for DMS replication instances"
  vpc_id      = aws_vpc.main.id

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-dms-sg"
  }
}

# Allow DMS replication instance to access RDS (when using our DMS security group)
resource "aws_security_group_rule" "rds_from_dms_internal" {
  count = var.enable_dms_access && var.dms_replication_instance_sg_id == null ? 1 : 0

  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.dms[0].id
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from DMS replication instance"
}

# Allow external DMS replication instance to access RDS (when SG ID is provided, same VPC)
resource "aws_security_group_rule" "rds_from_dms_external" {
  count = var.enable_dms_access && var.dms_replication_instance_sg_id != null && var.dms_cidr_block == null ? 1 : 0

  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = var.dms_replication_instance_sg_id
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from external DMS replication instance"
}

# Allow external DMS replication instance to access RDS (when CIDR block is provided, different VPC)
resource "aws_security_group_rule" "rds_from_dms_cidr" {
  count = var.enable_dms_access && var.dms_cidr_block != null ? 1 : 0

  type              = "ingress"
  from_port         = 3306
  to_port           = 3306
  protocol          = "tcp"
  cidr_blocks       = [var.dms_cidr_block]
  security_group_id = aws_security_group.rds.id
  description       = "MySQL from DMS replication instance (cross-VPC)"
}

# Allow specific DMS instance IP to access RDS (when DMS instance IP is provided)
resource "aws_security_group_rule" "rds_from_dms_specific_ip" {
  count = var.enable_dms_access && var.dms_instance_ip != null ? 1 : 0

  type              = "ingress"
  from_port         = 3306
  to_port           = 3306
  protocol          = "tcp"
  cidr_blocks       = ["${var.dms_instance_ip}/32"]
  security_group_id = aws_security_group.rds.id
  description       = "MySQL from specific DMS instance IP"
}
