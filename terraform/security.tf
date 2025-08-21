# Security Groups
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # HTTP access - CloudFlare IPs when SSL enabled, or public when disabled
  ingress {
    description = var.enable_cloudflare_ssl ? "HTTP from CloudFlare" : "HTTP public access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.enable_cloudflare_ssl ? [
      "103.21.244.0/22",
      "103.22.200.0/22", 
      "103.31.4.0/22",
      "104.16.0.0/13",
      "104.24.0.0/14",
      "108.162.192.0/18",
      "131.0.72.0/22",
      "141.101.64.0/18",
      "162.158.0.0/15",
      "172.64.0.0/13",
      "173.245.48.0/20",
      "188.114.96.0/20",
      "190.93.240.0/20",
      "197.234.240.0/22",
      "198.41.128.0/17"
    ] : ["0.0.0.0/0"]
  }

  # HTTPS access - only when CloudFlare SSL is enabled
  dynamic "ingress" {
    for_each = var.enable_cloudflare_ssl ? [1] : []
    content {
      description = "HTTPS from CloudFlare"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [
        "103.21.244.0/22",
        "103.22.200.0/22", 
        "103.31.4.0/22",
        "104.16.0.0/13",
        "104.24.0.0/14",
        "108.162.192.0/18",
        "131.0.72.0/22",
        "141.101.64.0/18",
        "162.158.0.0/15",
        "172.64.0.0/13",
        "173.245.48.0/20",
        "188.114.96.0/20",
        "190.93.240.0/20",
        "197.234.240.0/22",
        "198.41.128.0/17"
      ]
    }
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
  count = var.enable_dms_access && var.dms_replication_instance_sg_id == null && var.dms_instance_ip == null ? 1 : 0

  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.dms[0].id
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from DMS replication instance"
}

# Allow external DMS replication instance to access RDS (when SG ID is provided)
resource "aws_security_group_rule" "rds_from_dms_external" {
  count = var.enable_dms_access && var.dms_replication_instance_sg_id != null && var.dms_cidr_block == null && var.dms_instance_ip == null ? 1 : 0

  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = var.dms_replication_instance_sg_id
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from DMS replication instance (serverless)"
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
