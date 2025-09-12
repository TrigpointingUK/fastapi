# DynamoDB table for Terraform state locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "tuk-terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "tuk-terraform-state-lock"
    Project     = var.project_name
    Environment = "common"
    ManagedBy   = "terraform"
  }
}
