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

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
  default     = []
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = ""
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
