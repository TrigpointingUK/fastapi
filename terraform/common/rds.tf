# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "fastapi-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "fastapi-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "mysql8.0"
  name   = "fastapi-db-params"

  parameter {
    name         = "innodb_buffer_pool_size"
    value        = "{DBInstanceClassMemory*3/4}"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "immediate"
  }

  parameter {
    name         = "log_queries_not_using_indexes"
    value        = "1"
    apply_method = "immediate"
  }

  lifecycle {
    ignore_changes = [
      parameter
    ]
  }

  tags = {
    Name = "fastapi-db-params"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "fastapi-db"

  # Engine
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  # Database
  db_name = "fastapi_common"

  # Storage
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Maintenance
  parameter_group_name       = aws_db_parameter_group.main.name
  backup_retention_period    = 7
  backup_window              = "03:00-04:00"
  maintenance_window         = "Sun:04:00-Sun:05:00"
  auto_minor_version_upgrade = false

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  # Security
  deletion_protection       = false
  skip_final_snapshot       = false
  final_snapshot_identifier = "fastapi-final-snapshot"

  # Initial admin user
  username = "admin"
  # Password is managed by AWS when manage_master_user_password is true

  # Password rotation
  manage_master_user_password = true

  # Performance Insights (enabled with Database Insights Advanced mode)
  performance_insights_enabled = true
  performance_insights_retention_period = 465

  tags = {
    Name = "fastapi-db"
  }
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "fastapi-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "fastapi-rds-monitoring-role"
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
