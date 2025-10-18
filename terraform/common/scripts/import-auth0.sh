#!/bin/bash
set -e

# Import existing Auth0 resources into Terraform state
#
# Prerequisites:
# 1. Run fetch-auth0-ids.sh to get all resource IDs
# 2. Update the IDs below with the actual values from your Auth0 tenant
# 3. Run this script from terraform/common directory:
#    cd terraform/common && ./scripts/import-auth0.sh

echo "=========================================="
echo "   Importing Auth0 Resources"
echo "=========================================="
echo ""

# Change to terraform/common directory
cd "$(dirname "$0")/.."

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

echo "📊 Importing Database Connections..."

# TODO: Replace with actual connection IDs from fetch-auth0-ids.sh output
terraform import auth0_connection.tme_users "con_XXXXXXXXXX"
terraform import auth0_connection.tuk_users "con_YYYYYYYYYY"

echo "✅ Database connections imported"
echo ""

# ============================================================================
# RESOURCE SERVERS (APIs)
# ============================================================================

echo "🔌 Importing APIs (Resource Servers)..."

# TODO: Replace with actual resource server IDs
terraform import auth0_resource_server.api_tme "XXXXXXXXXX"
terraform import auth0_resource_server.api_tuk "YYYYYYYYYY"
terraform import auth0_resource_server.fastapi_tuk "ZZZZZZZZZZ"

echo "✅ APIs imported"
echo ""

# ============================================================================
# CLIENTS (APPLICATIONS)
# ============================================================================

echo "📱 Importing Clients (Applications)..."

# M2M Clients
terraform import auth0_client.api_tme "7OkFtciXsTEE3glKFwEtyJbIIgxJO7X2"
terraform import auth0_client.api_tuk "X4QQSV9ZEqzVww9ffPJr85hzmq0k2iYu"
terraform import auth0_client.fastapi_tuk "GyUTBYKq6W07oqx7p9Q3w1s3yAbrDcnw"

# SPA Client
terraform import auth0_client.swagger_ui "XovsHDHg8cijtoZmahlIZWsRi9zkObOu"

# Regular Web Clients
terraform import auth0_client.legacy "Ji5XbhuRT0EqLD3CrO8Onk8nDVbOfZFr"
terraform import auth0_client.trigpointinguk "j9EngSws9IkXjiuMXyF0GVqBEOC9DAaE"

# Native Client
terraform import auth0_client.android "IEBodjQvHMuDTS5vNVeve5j8YKQcYBN3"

echo "✅ Clients imported"
echo ""

# ============================================================================
# CLIENT GRANTS
# ============================================================================

echo "🔐 Importing Client Grants..."

# Client grants format: <client_id>:<audience>
# TODO: Update audience values with actual identifiers

# api-tme to api-tme
terraform import auth0_client_grant.api_tme_to_api_tme "7OkFtciXsTEE3glKFwEtyJbIIgxJO7X2:https://api.trigpointing.me/"

# api-tuk to api-tuk
terraform import auth0_client_grant.api_tuk_to_api_tuk "X4QQSV9ZEqzVww9ffPJr85hzmq0k2iYu:https://api.trigpointing.uk/"

# fastapi-tuk to fastapi-tuk
terraform import auth0_client_grant.fastapi_tuk_to_fastapi_tuk "GyUTBYKq6W07oqx7p9Q3w1s3yAbrDcnw:https://fastapi.trigpointing.uk/api/v1/"

# M2M clients to Management API
terraform import auth0_client_grant.api_tme_to_mgmt_api "7OkFtciXsTEE3glKFwEtyJbIIgxJO7X2:https://trigpointing.eu.auth0.com/api/v2/"
terraform import auth0_client_grant.api_tuk_to_mgmt_api "X4QQSV9ZEqzVww9ffPJr85hzmq0k2iYu:https://trigpointing.eu.auth0.com/api/v2/"

echo "✅ Client grants imported"
echo ""

# ============================================================================
# ROLES
# ============================================================================

echo "👥 Importing Roles..."

# TODO: Replace with actual role IDs from fetch-auth0-ids.sh output
terraform import auth0_role.tme_admin "rol_XXXXXXXXXX"
terraform import auth0_role.tuk_admin "rol_YYYYYYYYYY"

echo "✅ Roles imported"
echo ""

# ============================================================================
# ROLE PERMISSIONS
# ============================================================================

echo "🔑 Importing Role Permissions..."

# Role permissions format: <role_id>:<resource_server_identifier>:<permission_name>
# These will need to be imported individually for each permission

# TODO: Update with actual role IDs and resource server identifiers
# Example:
# terraform import auth0_role_permissions.tme_admin_perms "rol_XXX"
# terraform import auth0_role_permissions.tuk_admin_perms "rol_YYY"

echo "⚠️  Role permissions need to be imported manually (see comments in script)"
echo ""

# ============================================================================
# ACTIONS (Skip - these are new resources)
# ============================================================================

echo "⚡ Skipping Actions (new resources - will be created)..."
echo ""

# ============================================================================
# TRIGGER ACTIONS (Skip - these are new resources)
# ============================================================================

echo "🎯 Skipping Trigger Actions (new resources - will be created)..."
echo ""

echo "=========================================="
echo "✅ Import Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review any import errors above"
echo "2. Run: terraform plan"
echo "3. Fix any differences between Terraform config and actual state"
echo "4. Once plan looks good, the Actions will be created on apply"
echo ""
echo "Note: Some resources may need manual adjustment in auth0.tf to match"
echo "      the exact configuration in your Auth0 tenant."

