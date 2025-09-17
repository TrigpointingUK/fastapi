# DMS Serverless Migration Tasks for Staging and Production
# These use the new DMS Serverless mode for migration tasks

# Data source for the legacy source endpoint
data "aws_dms_endpoint" "legacy_source" {
  endpoint_id = "fastapi-legacy-source"
}

# DMS Serverless Migration Task for Staging
resource "aws_dms_replication_config" "staging_migration" {
  replication_config_identifier = "fastapi-staging-migration"
  replication_type              = "full-load"

  source_endpoint_arn = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn = aws_dms_endpoint.staging_target.endpoint_arn

  # Serverless configuration
  compute_config {
    replication_subnet_group_id  = aws_dms_replication_subnet_group.main.id
    vpc_security_group_ids       = [aws_security_group.dms.id]
    max_capacity_units           = 16
    min_capacity_units           = 2
    preferred_maintenance_window = "sun:10:30-sun:14:30"
  }

  # Table mappings
  table_mappings = jsonencode({
    rules = [
      {
        rule-type = "selection"
        rule-id   = "1"
        rule-name = "trigpoin_trigs_schema"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "include"
      },
      {
        rule-type = "transformation"
        rule-id   = "2"
        rule-name = "rename_schema"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "rename"
        value       = "tuk_staging"
        target-schema-name = "tuk_staging"
        rule-target = "schema"
      }
    ]
  })

  # Migration settings
  start_replication = false

  tags = {
    Name        = "fastapi-staging-migration"
    Environment = "staging"
    Type        = "dms-serverless-migration"
  }
}

# DMS Serverless Migration Task for Production
resource "aws_dms_replication_config" "production_migration" {
  replication_config_identifier = "fastapi-production-migration"
  replication_type              = "full-load"

  source_endpoint_arn = data.aws_dms_endpoint.legacy_source.endpoint_arn
  target_endpoint_arn = aws_dms_endpoint.production_target.endpoint_arn

  # Serverless configuration
  compute_config {
    replication_subnet_group_id  = aws_dms_replication_subnet_group.main.id
    vpc_security_group_ids       = [aws_security_group.dms.id]
    max_capacity_units           = 16
    min_capacity_units           = 2
    preferred_maintenance_window = "sun:10:30-sun:14:30"
  }

  # Table mappings
  table_mappings = jsonencode({
    rules = [
      {
        rule-type = "selection"
        rule-id   = "1"
        rule-name = "trigpoin_trigs_schema"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "include"
      },
      {
        rule-type = "transformation"
        rule-id   = "2"
        rule-name = "rename_schema"
        object-locator = {
          schema-name = "trigpoin_trigs"
          table-name  = "%"
        }
        rule-action = "rename"
        value       = "tuk_production"
        target-schema-name = "tuk_production"
        rule-target = "schema"
      }
    ]
  })

  # Migration settings
  start_replication = false

  tags = {
    Name        = "fastapi-production-migration"
    Environment = "production"
    Type        = "dms-serverless-migration"
  }
}
