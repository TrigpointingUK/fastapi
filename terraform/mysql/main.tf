terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    mysql = {
      source  = "petoju/mysql"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    # Backend configuration will be provided via backend.conf files
    # Use: terraform init -backend-config=backend.conf
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "mysql"
      ManagedBy   = "terraform"
    }
  }
}

# Data sources for remote state
data "terraform_remote_state" "common" {
  backend = "s3"
  config = {
    bucket = "tuk-terraform-state"
    key    = "fastapi-common/terraform.tfstate"
    region = "eu-west-1"
  }
}

# MySQL provider for database management
provider "mysql" {
  endpoint = data.terraform_remote_state.common.outputs.rds_endpoint
  username = "admin"
  password = random_password.admin_password.result
}
