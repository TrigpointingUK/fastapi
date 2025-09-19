# Parameter Store Best Practices: Object vs Individual Variables

## Current Approach (Not Recommended) ❌

```hcl
# Too many individual variables - hard to maintain
variable "xray_enabled" { type = bool }
variable "xray_service_name" { type = string }
variable "xray_sampling_rate" { type = number }
variable "xray_daemon_address" { type = string }
variable "log_level" { type = string }
variable "cors_origins" { type = string }
variable "db_pool_size" { type = number }
variable "db_pool_recycle" { type = number }
# ... 20+ more variables
```

**Problems:**
- ❌ Verbose and repetitive
- ❌ Hard to maintain
- ❌ Difficult to add new parameters
- ❌ No logical grouping
- ❌ Prone to typos and inconsistencies

## Recommended Approaches ✅

### Option 1: Structured Object (Best for Most Cases)

```hcl
variable "parameter_store_config" {
  type = object({
    enabled = optional(bool, false)
    parameters = optional(object({
      xray = optional(object({
        enabled        = optional(bool, false)
        service_name   = optional(string, "trigpointing-api")
        sampling_rate  = optional(number, 0.1)
        daemon_address = optional(string, null)
      }), {})
      app = optional(object({
        log_level    = optional(string, "INFO")
        cors_origins = optional(string, null)
      }), {})
      database = optional(object({
        pool_size    = optional(number, 5)
        pool_recycle = optional(number, 300)
      }), {})
    }), {})
  })
  default = {}
}
```

**Usage:**
```hcl
# terraform.tfvars
parameter_store_config = {
  enabled = true
  parameters = {
    xray = {
      enabled        = true
      service_name   = "trigpointing-api-staging"
      sampling_rate  = 0.2
    }
    app = {
      log_level    = "DEBUG"
      cors_origins = "https://staging.trigpointing.uk"
    }
    database = {
      pool_size    = 5
      pool_recycle = 300
    }
  }
}
```

**Benefits:**
- ✅ Logical grouping
- ✅ Type safety
- ✅ Default values
- ✅ Easy to extend
- ✅ Self-documenting

### Option 2: Simple Map (Most Flexible)

```hcl
variable "parameter_store_parameters" {
  type = map(object({
    value = string
    type  = optional(string, "String")
    description = optional(string, "")
  }))
  default = {}
}
```

**Usage:**
```hcl
# terraform.tfvars
parameter_store_parameters = {
  "xray/enabled" = {
    value = "true"
    description = "Enable X-Ray tracing"
  }
  "xray/service_name" = {
    value = "trigpointing-api-staging"
    description = "X-Ray service name"
  }
  "app/log_level" = {
    value = "DEBUG"
    description = "Application log level"
  }
}
```

**Benefits:**
- ✅ Maximum flexibility
- ✅ Easy to add any parameter
- ✅ Simple structure
- ✅ Good for dynamic configurations

### Option 3: Environment-Specific (Most Scalable)

```hcl
variable "environment_config" {
  type = object({
    parameter_store = optional(object({
      enabled = bool
      parameters = map(object({
        value = string
        type  = optional(string, "String")
        description = optional(string, "")
      }))
    }), null)
  })
  default = {}
}
```

**Benefits:**
- ✅ Environment-specific configs
- ✅ Easy to manage multiple environments
- ✅ Can include other environment settings
- ✅ Good for complex deployments

## Implementation Comparison

### Current Approach (Individual Variables)
```hcl
# 20+ individual resources
resource "aws_ssm_parameter" "xray_enabled" {
  name  = "/${var.project_name}/${var.environment}/xray/enabled"
  value = var.xray_enabled ? "true" : "false"
  # ... repeat for each parameter
}
```

### Improved Approach (Dynamic Creation)
```hcl
# Single resource with for_each
resource "aws_ssm_parameter" "parameters" {
  for_each = var.parameter_store_config.enabled ? local.parameter_map : {}

  name  = "/${var.project_name}/${var.environment}/${each.key}"
  value = each.value.value
  type  = each.value.type

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = each.key
  }
}
```

## Migration Strategy

### Step 1: Add New Object-Based Variables
```hcl
# Add to variables.tf
variable "parameter_store_config" {
  # ... object definition
}
```

### Step 2: Create Dynamic Parameter Resources
```hcl
# Add to parameter_store.tf
resource "aws_ssm_parameter" "parameters" {
  for_each = var.parameter_store_config.enabled ? local.parameter_map : {}
  # ... dynamic creation
}
```

### Step 3: Update ECS Task Definition
```hcl
# Update main.tf
secrets = concat([
  # ... existing secrets
  var.parameter_store_config.enabled ? [
    for key, param in local.parameter_map : {
      name      = upper(replace(key, "/", "_"))
      valueFrom = aws_ssm_parameter.parameters[key].arn
    }
  ] : []
])
```

### Step 4: Update terraform.tfvars
```hcl
# Replace individual variables with object
parameter_store_config = {
  enabled = true
  parameters = {
    xray = {
      enabled        = true
      service_name   = "trigpointing-api-staging"
      sampling_rate  = 0.2
    }
    # ... other groups
  }
}
```

### Step 5: Remove Old Variables
```hcl
# Remove individual variables
# variable "xray_enabled" { ... }
# variable "xray_service_name" { ... }
# ... etc
```

## Best Practices Summary

1. **Use Objects for Related Parameters** - Group related settings together
2. **Use Maps for Dynamic Parameters** - When you need maximum flexibility
3. **Use Optional Fields** - Make parameters optional with defaults
4. **Use Descriptive Names** - Make parameter names self-documenting
5. **Use Type Safety** - Define proper types for all parameters
6. **Use Local Values** - Build complex maps in locals for readability
7. **Use for_each** - Create resources dynamically instead of individually
8. **Use Tags** - Tag parameters for better organization
9. **Use Hierarchical Names** - Use forward slashes for parameter hierarchy
10. **Use Documentation** - Document all parameters and their purposes

## When to Use Each Approach

- **Structured Object**: When you have a known set of related parameters
- **Simple Map**: When you need maximum flexibility and dynamic parameters
- **Environment-Specific**: When you have complex environment-specific configurations
- **Individual Variables**: Only for truly independent, unrelated parameters

The object-based approach is generally recommended as it provides the best balance of type safety, maintainability, and flexibility.
