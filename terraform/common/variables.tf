variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"  # London region
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "fastapi"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["eu-west-2a", "eu-west-2b"]
}

variable "admin_ip_address" {
  description = "IP address allowed to connect to bastion host"
  type        = string
  default     = "86.162.34.238"  # Your admin IP
}

variable "key_pair_name" {
  description = "AWS key pair name for bastion host access"
  type        = string
  default     = "fastapi-bastion"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

# DMS Variables
variable "legacy_mysql_host" {
  description = "Hostname or IP of the legacy MySQL server"
  type        = string
  default     = ""
}

variable "legacy_mysql_username" {
  description = "Username for the legacy MySQL server"
  type        = string
  default     = ""
  sensitive   = true
}

variable "legacy_mysql_password" {
  description = "Password for the legacy MySQL server"
  type        = string
  default     = ""
  sensitive   = true
}

variable "legacy_mysql_database" {
  description = "Database name on the legacy MySQL server"
  type        = string
  default     = ""
}

variable "dms_table_mappings" {
  description = "DMS table mappings for replication"
  type        = string
  default     = <<EOF
{
  "rules": [
    {
      "rule-type": "selection",
      "rule-id": "1",
      "rule-name": "1",
      "object-locator": {
        "schema-name": "%",
        "table-name": "%"
      },
      "rule-action": "include"
    }
  ]
}
EOF
}
