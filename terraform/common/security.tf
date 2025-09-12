# Security Groups
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
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

  # MySQL access from DMS
  ingress {
    description     = "MySQL from DMS"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.dms.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

# DMS Security Group
resource "aws_security_group" "dms" {
  name        = "${var.project_name}-dms-sg"
  description = "Security group for DMS replication instance"
  vpc_id      = aws_vpc.main.id

  # MySQL access to RDS (target)
  egress {
    description = "MySQL to RDS"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # MySQL access to legacy EC2 (source) - will be updated with specific IP
  egress {
    description = "MySQL to legacy EC2"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Will be restricted to legacy EC2 IP
  }

  # SSH access for DMS instance management
  ingress {
    description = "SSH for DMS management"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-dms-sg"
  }
}
