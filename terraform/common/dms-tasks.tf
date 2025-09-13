# DMS Serverless Replication Configs for Staging and Production
# These use DMS serverless mode which doesn't require a replication instance

# Data source for the legacy source endpoint
data "aws_dms_endpoint" "legacy_source" {
  endpoint_id = "legacy-fastapi"
}

# DMS Replication Subnet Group (required for serverless)
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

# DMS Replication Config for Staging (Serverless Mode)
resource "aws_dms_replication_config" "staging" {
  replication_config_identifier = "${var.project_name}-staging-migration"
  replication_type              = "full-load"
  source_endpoint_arn           = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn           = aws_dms_endpoint.staging_user.endpoint_arn

  table_mappings = jsonencode({
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

  replication_settings = jsonencode({
    TargetMetadata = {
      TargetSchema = "tuk_staging"
      SupportLobs  = true
      FullLobMode   = false
    }
    FullLoadSettings = {
      TargetTablePrepMode = "DROP_AND_CREATE"
      CreatePkAfterFullLoad = false
      StopTaskCachedChangesNotApplied = false
    }
    Logging = {
      EnableLogging = true
    }
  })

  compute_config {
    max_capacity_units           = 2
    min_capacity_units           = 1
    multi_az                     = false
    replication_subnet_group_id  = aws_dms_replication_subnet_group.main.id
    vpc_security_group_ids       = [aws_security_group.dms.id]
  }

  tags = {
    Name        = "${var.project_name}-staging-migration"
    Environment = "staging"
    Type        = "serverless"
  }
}

# DMS Replication Config for Production (Serverless Mode)
resource "aws_dms_replication_config" "production" {
  replication_config_identifier = "${var.project_name}-production-migration"
  replication_type              = "full-load"
  source_endpoint_arn           = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn           = aws_dms_endpoint.production_user.endpoint_arn

  table_mappings = jsonencode({
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

  replication_settings = jsonencode({
    TargetMetadata = {
      TargetSchema = "tuk_production"
      SupportLobs  = true
      FullLobMode   = false
    }
    FullLoadSettings = {
      TargetTablePrepMode = "DROP_AND_CREATE"
      CreatePkAfterFullLoad = false
      StopTaskCachedChangesNotApplied = false
    }
    Logging = {
      EnableLogging = true
    }
  })

  compute_config {
    max_capacity_units           = 2
    min_capacity_units           = 1
    multi_az                     = false
    replication_subnet_group_id  = aws_dms_replication_subnet_group.main.id
    vpc_security_group_ids       = [aws_security_group.dms.id]
  }

  tags = {
    Name        = "${var.project_name}-production-migration"
    Environment = "production"
    Type        = "serverless"
  }
}
