# DMS Target Endpoints for Staging and Production
# These use the existing credentials secrets to access the common RDS database

# Data source for mysql remote state to get secret ARNs
data "terraform_remote_state" "mysql" {
  backend = "s3"
  config = {
    bucket = "tuk-terraform-state"
    key    = "fastapi-mysql/terraform.tfstate"
    region = "eu-west-1"
  }
}

# Data sources for secret values
data "aws_secretsmanager_secret_version" "staging_credentials" {
  secret_id = data.terraform_remote_state.mysql.outputs.staging_credentials_arn
}

data "aws_secretsmanager_secret_version" "production_credentials" {
  secret_id = data.terraform_remote_state.mysql.outputs.production_credentials_arn
}

# DMS Replication Subnet Group (required for DMS)
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

  tags = {
    Name        = "${var.project_name}-dms"
    Environment = "common"
  }
}

# Allow DMS general internet access (for AWS services, etc.)
resource "aws_security_group_rule" "dms_internet_access" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.dms.id
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

# IAM role for DMS to access secrets and RDS
resource "aws_iam_role" "dms_service_role" {
  name = "${var.project_name}-dms-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "dms.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-dms-service-role"
    Environment = "common"
  }
}

# IAM policy for DMS to access secrets
resource "aws_iam_policy" "dms_secrets_access" {
  name        = "${var.project_name}-dms-secrets-access"
  description = "Policy for DMS to access credentials secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          data.terraform_remote_state.mysql.outputs.staging_credentials_arn,
          data.terraform_remote_state.mysql.outputs.production_credentials_arn
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-dms-secrets-access"
    Environment = "common"
  }
}

# Attach the secrets policy to the DMS role
resource "aws_iam_role_policy_attachment" "dms_secrets_access" {
  role       = aws_iam_role.dms_service_role.name
  policy_arn = aws_iam_policy.dms_secrets_access.arn
}

# Attach the DMS service role policy
resource "aws_iam_role_policy_attachment" "dms_service_role" {
  role       = aws_iam_role.dms_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonDMSVPCManagementRole"
}

# DMS Target Endpoint for Staging
resource "aws_dms_endpoint" "staging_target" {
  endpoint_id   = "fastapi-staging-target"
  endpoint_type = "target"
  engine_name   = "mysql"
  server_name   = split(":", aws_db_instance.main.endpoint)[0]
  port          = aws_db_instance.main.port
  username      = jsondecode(data.aws_secretsmanager_secret_version.staging_credentials.secret_string)["username"]
  password      = jsondecode(data.aws_secretsmanager_secret_version.staging_credentials.secret_string)["password"]
  database_name = jsondecode(data.aws_secretsmanager_secret_version.staging_credentials.secret_string)["dbname"]
  ssl_mode      = "none"

  tags = {
    Name        = "fastapi-staging-target"
    Environment = "staging"
    Type        = "dms-target"
  }
}

# DMS Target Endpoint for Production
resource "aws_dms_endpoint" "production_target" {
  endpoint_id   = "fastapi-production-target"
  endpoint_type = "target"
  engine_name   = "mysql"
  server_name   = split(":", aws_db_instance.main.endpoint)[0]
  port          = aws_db_instance.main.port
  username      = jsondecode(data.aws_secretsmanager_secret_version.production_credentials.secret_string)["username"]
  password      = jsondecode(data.aws_secretsmanager_secret_version.production_credentials.secret_string)["password"]
  database_name = jsondecode(data.aws_secretsmanager_secret_version.production_credentials.secret_string)["dbname"]
  ssl_mode      = "none"

  tags = {
    Name        = "fastapi-production-target"
    Environment = "production"
    Type        = "dms-target"
  }
}
