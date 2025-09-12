# Simple admin password for RDS initial setup
# The mysql/ directory will manage the full user/schema configuration
resource "random_password" "admin_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}
