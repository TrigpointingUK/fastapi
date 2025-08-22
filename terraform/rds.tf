# RDS Subnet Group (only when using managed RDS)
resource "aws_db_subnet_group" "main" {
  count = var.use_external_database ? 0 : 1

  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

# RDS Parameter Group (only when using managed RDS)
resource "aws_db_parameter_group" "main" {
  count = var.use_external_database ? 0 : 1

  family = "mysql8.0"
  name   = "${var.project_name}-${var.environment}-db-params"

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
    Name = "${var.project_name}-${var.environment}-db-params"
  }
}

# RDS Instance (only when using managed RDS)
resource "aws_db_instance" "main" {
  count = var.use_external_database ? 0 : 1

  identifier = "${var.project_name}-${var.environment}-db"

  # Engine
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.environment == "production" ? "db.t3.medium" : "db.t3.micro"

  # Database
  db_name  = "${var.project_name}_${var.environment}"
  username = var.db_username
  password = var.db_password

  # Storage
  allocated_storage     = var.environment == "production" ? 100 : 20
  max_allocated_storage = var.environment == "production" ? 1000 : 100
  storage_type          = "gp2"
  storage_encrypted     = true

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  publicly_accessible    = var.environment == "staging" ? true : false

  # Maintenance
  parameter_group_name   = aws_db_parameter_group.main[0].name
  backup_retention_period = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"
  auto_minor_version_upgrade = false

  # Monitoring
  monitoring_interval = var.environment == "production" ? 60 : 0
  monitoring_role_arn = var.environment == "production" ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  # Security
  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  # Performance Insights
  performance_insights_enabled = var.environment == "production" ? true : false

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}

# RDS Enhanced Monitoring Role (for production only)
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.environment == "production" ? 1 : 0

  name = "${var.project_name}-${var.environment}-rds-monitoring-role"

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
    Name = "${var.project_name}-${var.environment}-rds-monitoring-role"
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.environment == "production" ? 1 : 0

  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
