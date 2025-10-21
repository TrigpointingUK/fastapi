#!/bin/bash
# get-auth0-ids.sh - Extract Auth0 resource IDs for import
#
# Usage:
#   1. Set environment variables (matches staging naming convention):
#      export AUTH0_TENANT_DOMAIN="trigpointing.eu.auth0.com"
#      export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID="<terraform_provider_client_id>"
#      export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET="<terraform_provider_secret>"
#   2. Run: ./scripts/get-auth0-ids.sh
#
# Note: Use Terraform provider credentials, NOT FastAPI M2M credentials
# This script will output all resource IDs needed for terraform import

set -e

# Configuration - Update these or set via environment variables
# Use the same naming convention as staging
AUTH0_DOMAIN="${AUTH0_TENANT_DOMAIN:-}"
TERRAFORM_CLIENT_ID="${AUTH0_TERRAFORM_PROVIDER_CLIENT_ID:-}"
TERRAFORM_CLIENT_SECRET="${AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET:-}"

# Check prerequisites
if [ -z "$AUTH0_DOMAIN" ]; then
    echo "ERROR: Missing AUTH0_TENANT_DOMAIN!"
    echo "Please set AUTH0_TENANT_DOMAIN environment variable"
    echo ""
    echo "Example:"
    echo "  export AUTH0_TENANT_DOMAIN='trigpointing.eu.auth0.com'"
    echo "  export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID='<terraform_provider_client_id>'"
    echo "  export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET='<terraform_provider_client_secret>'"
    echo "  ./scripts/get-auth0-ids.sh"
    exit 1
fi

if [ -z "$TERRAFORM_CLIENT_ID" ] || [ -z "$TERRAFORM_CLIENT_SECRET" ]; then
    echo "ERROR: Missing Terraform provider credentials!"
    echo "Please set AUTH0_TERRAFORM_PROVIDER_CLIENT_ID and AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET"
    echo ""
    echo "These are the credentials for the Terraform Management M2M application"
    echo "(NOT the FastAPI M2M application)"
    echo ""
    echo "Example:"
    echo "  export AUTH0_TENANT_DOMAIN='trigpointing.eu.auth0.com'"
    echo "  export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID='<terraform_provider_client_id>'"
    echo "  export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET='<terraform_provider_client_secret>'"
    echo "  ./scripts/get-auth0-ids.sh"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required but not installed."
    echo "Install with: sudo apt-get install jq"
    exit 1
fi

echo "Fetching Auth0 resource IDs from ${AUTH0_DOMAIN}..."
echo ""

# Get access token
echo "Getting Management API access token..."
TOKEN_RESPONSE=$(curl -s --request POST \
  --url "https://${AUTH0_DOMAIN}/oauth/token" \
  --header 'content-type: application/json' \
  --data "{\"grant_type\":\"client_credentials\",\"client_id\":\"${TERRAFORM_CLIENT_ID}\",\"client_secret\":\"${TERRAFORM_CLIENT_SECRET}\",\"audience\":\"https://${AUTH0_DOMAIN}/api/v2/\"}")

# Check for errors in response
if echo "$TOKEN_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    echo "ERROR: Failed to authenticate with Auth0"
    echo "Response: $TOKEN_RESPONSE"
    echo ""
    echo "Common causes:"
    echo "  - Incorrect AUTH0_TENANT_DOMAIN"
    echo "  - Invalid Terraform provider client ID or secret"
    echo "  - Terraform provider M2M app not authorized for Management API"
    echo "  - Using wrong credentials (use Terraform provider, NOT FastAPI M2M credentials)"
    exit 1
fi

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get access token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✓ Access token obtained"
echo ""

# Get all connections
echo "=========================================="
echo "CONNECTIONS"
echo "=========================================="
CONNECTIONS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/connections")
if echo "$CONNECTIONS" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$CONNECTIONS" | jq -r '.[] | "Name: \(.name)\nID: \(.id)\nStrategy: \(.strategy)\n---"'
else
    echo "ERROR: Unexpected response from connections API"
    echo "$CONNECTIONS" | jq '.'
fi
echo ""

# Get all clients
echo "=========================================="
echo "CLIENTS (APPLICATIONS)"
echo "=========================================="
CLIENTS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/clients?fields=client_id,name,app_type&include_fields=true")
if echo "$CLIENTS" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$CLIENTS" | jq -r '.[] | "Name: \(.name)\nClient ID: \(.client_id)\nType: \(.app_type)\n---"'
else
    echo "ERROR: Unexpected response from clients API"
    echo "$CLIENTS" | jq '.'
fi
echo ""

# Get all resource servers (APIs)
echo "=========================================="
echo "RESOURCE SERVERS (APIs)"
echo "=========================================="
APIS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/resource-servers")
if echo "$APIS" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$APIS" | jq -r '.[] | "Name: \(.name)\nIdentifier: \(.identifier)\nID: \(.id)\n---"'
else
    echo "ERROR: Unexpected response from resource-servers API"
    echo "$APIS" | jq '.'
fi
echo ""

# Get all roles
echo "=========================================="
echo "ROLES"
echo "=========================================="
ROLES=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/roles")
if echo "$ROLES" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$ROLES" | jq -r '.[] | "Name: \(.name)\nID: \(.id)\n---"'
else
    echo "ERROR: Unexpected response from roles API"
    echo "$ROLES" | jq '.'
fi
echo ""

# Get all actions
echo "=========================================="
echo "ACTIONS"
echo "=========================================="
ACTIONS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/actions/actions")
if echo "$ACTIONS" | jq -e '.actions' > /dev/null 2>&1; then
    echo "$ACTIONS" | jq -r '.actions[]? | "Name: \(.name)\nID: \(.id)\nTrigger: \(.supported_triggers[0].id)\n---"'
    if [ $(echo "$ACTIONS" | jq '.actions | length') -eq 0 ]; then
        echo "(No actions found)"
    fi
else
    echo "ERROR: Unexpected response from actions API"
    echo "$ACTIONS" | jq '.'
fi
echo ""

# Get client grants
echo "=========================================="
echo "CLIENT GRANTS"
echo "=========================================="
GRANTS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/client-grants")
if echo "$GRANTS" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$GRANTS" | jq -r '.[] | "Grant ID: \(.id)\nClient ID: \(.client_id)\nAudience: \(.audience)\nScopes: \(.scope | join(", "))\n---"'
else
    echo "ERROR: Unexpected response from client-grants API"
    echo "$GRANTS" | jq '.'
fi
echo ""

# Get custom domains
echo "=========================================="
echo "CUSTOM DOMAINS"
echo "=========================================="
DOMAINS=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/custom-domains")
if echo "$DOMAINS" | jq -e 'type == "array"' > /dev/null 2>&1; then
    echo "$DOMAINS" | jq -r '.[] | "Domain: \(.domain)\nID: \(.custom_domain_id)\nType: \(.type)\nStatus: \(.status)\n---"'
    if [ $(echo "$DOMAINS" | jq '. | length') -eq 0 ]; then
        echo "(No custom domains found)"
    fi
else
    echo "ERROR: Unexpected response from custom-domains API"
    echo "$DOMAINS" | jq '.'
fi
echo ""

# Get branding
echo "=========================================="
echo "BRANDING"
echo "=========================================="
BRANDING=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/branding")
if echo "$BRANDING" | jq -e 'type == "object"' > /dev/null 2>&1; then
    echo "$BRANDING" | jq -r '"Logo URL: \(.logo_url // "not set")\nPrimary Color: \(.colors.primary // "not set")\nPage Background: \(.colors.page_background // "not set")"'
else
    echo "ERROR: Unexpected response from branding API"
    echo "$BRANDING" | jq '.'
fi
echo ""

# Get tenant settings
echo "=========================================="
echo "TENANT SETTINGS"
echo "=========================================="
TENANT=$(curl -s -H "Authorization: Bearer $TOKEN" "https://${AUTH0_DOMAIN}/api/v2/tenants/settings")
if echo "$TENANT" | jq -e 'type == "object"' > /dev/null 2>&1; then
    echo "$TENANT" | jq -r '"Friendly Name: \(.friendly_name // "not set")\nPicture URL: \(.picture_url // "not set")\nSupport Email: \(.support_email // "not set")\nSupport URL: \(.support_url // "not set")"'
else
    echo "ERROR: Unexpected response from tenant settings API"
    echo "$TENANT" | jq '.'
fi
echo ""

echo "=========================================="
echo "SUMMARY COMPLETE"
echo "=========================================="
echo ""
echo "Use these IDs in your terraform import commands."
echo "Save this output for reference during the import process."

