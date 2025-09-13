# DMS Serverless Replication Tasks for Staging and Production
# These use the DMS endpoints we created and reference the legacy source

# DMS Task for Staging
resource "aws_dms_replication_task" "staging" {
  migration_type             = "full-load"
  replication_instance_arn   = aws_dms_replication_instance.serverless.replication_instance_arn
  replication_task_id        = "${var.project_name}-staging-migration"
  source_endpoint_arn        = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn        = aws_dms_endpoint.staging_user.endpoint_arn
  table_mappings             = jsonencode({
    rules = [
      {
        rule-type = "selection"
        rule-id   = "1"
        rule-name = "trigpoin_trigs_selection"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "include"
      },
      {
        rule-type = "transformation"
        rule-id   = "2"
        rule-name = "trigpoin_trigs_rename"
        object-locator = {
          schema-name = "trigpoin_trigs"
        }
        rule-action = "rename"
        value       = "tuk_staging"
      }
    ]
  })
  start_replication_task = false
  tags = {
    Name        = "${var.project_name}-staging-migration"
    Environment = "staging"
    Type        = "serverless"
  }
}

# DMS Task for Production
resource "aws_dms_replication_task" "production" {
  migration_type             = "full-load"
  replication_instance_arn   = aws_dms_replication_instance.serverless.replication_instance_arn
  replication_task_id        = "${var.project_name}-production-migration"
  source_endpoint_arn        = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn        = aws_dms_endpoint.production_user.endpoint_arn
  table_mappings             = jsonencode({
    rules = [
      {
        rule-type = "selection"
        rule-id   = "1"
        rule-name = "trigpoin_trigs_selection"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "include"
      },
      {
        rule-type = "transformation"
        rule-id   = "2"
        rule-name = "trigpoin_trigs_rename"
        object-locator = {
          schema-name = "trigpoin_trigs"
        }
        rule-action = "rename"
        value       = "tuk_production"
      }
    ]
  })
  start_replication_task = false
  tags = {
    Name        = "${var.project_name}-production-migration"
    Environment = "production"
    Type        = "serverless"
  }
}

# Data source for the legacy source endpoint
data "aws_dms_endpoint" "legacy_source" {
  endpoint_id = "legacy-fastapi"
}

# DMS Serverless Replication Instance
resource "aws_dms_replication_instance" "serverless" {
  replication_instance_id     = "${var.project_name}-serverless"
  replication_instance_class  = "dms.serverless"
  allocated_storage           = 50
  apply_immediately           = true
  auto_minor_version_upgrade  = true
  engine_version              = "3.5.3"
  multi_az                    = false
  preferred_maintenance_window = "sun:10:30-sun:14:30"
  publicly_accessible         = false
  replication_subnet_group_id = aws_dms_replication_subnet_group.main.id
  vpc_security_group_ids      = [aws_security_group.dms.id]

  tags = {
    Name        = "${var.project_name}-serverless"
    Environment = "common"
    Type        = "serverless"
  }
}

# DMS Replication Subnet Group
resource "aws_dms_replication_subnet_group" "main" {
  replication_subnet_group_id          = "${var.project_name}-dms-subnet-group"
  replication_subnet_group_description = "DMS subnet group for ${var.project_name}"
  subnet_ids                           = aws_subnet.private[*].id

  tags = {
    Name        = "${var.project_name}-dms-subnet-group"
    Environment = "common"
  }
}

# Security Group for DMS
resource "aws_security_group" "dms" {
  name_prefix = "${var.project_name}-dms-"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-dms"
    Environment = "common"
  }
}

# Allow DMS to access RDS
resource "aws_security_group_rule" "dms_to_rds" {
  type                     = "egress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds.id
  security_group_id        = aws_security_group.dms.id
}
