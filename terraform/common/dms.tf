# DMS Replication Instance
resource "aws_dms_replication_instance" "main" {
  replication_instance_id     = "${var.project_name}-dms-replication"
  replication_instance_class  = "dms.t3.micro"
  allocated_storage           = 20
  apply_immediately           = true
  auto_minor_version_upgrade  = true
  engine_version              = "3.5.3"
  multi_az                    = false
  preferred_maintenance_window = "sun:10:30-sun:14:30"
  publicly_accessible         = false
  replication_subnet_group_id  = aws_dms_replication_subnet_group.main.id
  vpc_security_group_ids      = [aws_security_group.dms.id]

  tags = {
    Name = "${var.project_name}-dms-replication"
  }
}

# DMS Replication Subnet Group
resource "aws_dms_replication_subnet_group" "main" {
  replication_subnet_group_id          = "${var.project_name}-dms-subnet-group"
  replication_subnet_group_description = "DMS subnet group for ${var.project_name}"
  subnet_ids                           = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-dms-subnet-group"
  }
}

# DMS Source Endpoint (Legacy EC2 MySQL)
resource "aws_dms_endpoint" "source" {
  endpoint_id   = "${var.project_name}-source-mysql"
  endpoint_type = "source"
  engine_name   = "mysql"

  # These will need to be provided via variables or secrets
  server_name               = var.legacy_mysql_host
  port                      = 3306
  username                  = var.legacy_mysql_username
  password                  = var.legacy_mysql_password
  database_name             = var.legacy_mysql_database

  ssl_mode = "none" # Adjust based on your legacy setup

  tags = {
    Name = "${var.project_name}-source-mysql"
  }
}

# DMS Target Endpoint (New RDS MySQL)
resource "aws_dms_endpoint" "target" {
  endpoint_id   = "${var.project_name}-target-mysql"
  endpoint_type = "target"
  engine_name   = "mysql"

  server_name   = aws_db_instance.main.endpoint
  port          = aws_db_instance.main.port
  username      = "admin"
  password      = random_password.admin_password.result
  database_name = "fastapi_common"

  ssl_mode = "none" # RDS uses SSL by default, but DMS can handle this

  tags = {
    Name = "${var.project_name}-target-mysql"
  }
}

# DMS Replication Task
resource "aws_dms_replication_task" "main" {
  migration_type             = "full-load-and-cdc"
  replication_instance_arn   = aws_dms_replication_instance.main.replication_instance_arn
  replication_task_id        = "${var.project_name}-replication-task"
  source_endpoint_arn        = aws_dms_endpoint.source.endpoint_arn
  target_endpoint_arn        = aws_dms_endpoint.target.endpoint_arn
  table_mappings             = var.dms_table_mappings

  replication_task_settings = jsonencode({
    TargetMetadata = {
      TargetSchema = ""
      SupportLobs  = true
      FullLobMode  = false
    }
    FullLoadSettings = {
      TargetTablePrepMode = "DO_NOTHING"
      CreatePkAfterFullLoad = false
      StopTaskCachedChangesApplied = false
      StopTaskCachedChangesNotApplied = false
      MaxFullLoadSubTasks = 8
      TransactionConsistencyTimeout = 600
      CommitRate = 10000
    }
    Logging = {
      EnableLogging = true
    }
  })

  tags = {
    Name = "${var.project_name}-replication-task"
  }
}
