#!/bin/bash
set -e

# Fetch Auth0 Resource IDs for Terraform Import
# 
# This script uses the Auth0 Management API to retrieve all resource IDs
# needed for importing existing Auth0 resources into Terraform.
#
# Prerequisites:
# - Set AUTH0_DOMAIN environment variable
# - Set AUTH0_MANAGEMENT_API_TOKEN environment variable
#   (or provide M2M credentials to generate one)

if [ -z "$AUTH0_DOMAIN" ]; then
    echo "ERROR: AUTH0_DOMAIN environment variable not set"
    echo "Example: export AUTH0_DOMAIN=trigpointing.eu.auth0.com"
    exit 1
fi

if [ -z "$AUTH0_MANAGEMENT_API_TOKEN" ]; then
    echo "WARNING: AUTH0_MANAGEMENT_API_TOKEN not set"
    echo "Attempting to generate token using M2M credentials..."
    
    if [ -z "$AUTH0_M2M_CLIENT_ID" ] || [ -z "$AUTH0_M2M_CLIENT_SECRET" ]; then
        echo "ERROR: Need either AUTH0_MANAGEMENT_API_TOKEN or AUTH0_M2M_CLIENT_ID + AUTH0_M2M_CLIENT_SECRET"
        exit 1
    fi
    
    # Get M2M token
    TOKEN_RESPONSE=$(curl -s --request POST \
        --url "https://${AUTH0_DOMAIN}/oauth/token" \
        --header 'content-type: application/json' \
        --data "{
            \"client_id\":\"${AUTH0_M2M_CLIENT_ID}\",
            \"client_secret\":\"${AUTH0_M2M_CLIENT_SECRET}\",
            \"audience\":\"https://${AUTH0_DOMAIN}/api/v2/\",
            \"grant_type\":\"client_credentials\"
        }")
    
    AUTH0_MANAGEMENT_API_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
    
    if [ "$AUTH0_MANAGEMENT_API_TOKEN" == "null" ] || [ -z "$AUTH0_MANAGEMENT_API_TOKEN" ]; then
        echo "ERROR: Failed to get management API token"
        echo "$TOKEN_RESPONSE"
        exit 1
    fi
    
    echo "✅ Successfully obtained management API token"
fi

API_URL="https://${AUTH0_DOMAIN}/api/v2"

echo ""
echo "=========================================="
echo "   Auth0 Resource IDs for Terraform"
echo "=========================================="
echo ""

# Database Connections
echo "📊 DATABASE CONNECTIONS"
echo "----------------------"
curl -s --request GET \
    --url "${API_URL}/connections?strategy=auth0" \
    --header "authorization: Bearer ${AUTH0_MANAGEMENT_API_TOKEN}" | \
    jq -r '.[] | "Name: \(.name)\nID: \(.id)\n"'

# Resource Servers (APIs)
echo "🔌 APIS (Resource Servers)"
echo "--------------------------"
curl -s --request GET \
    --url "${API_URL}/resource-servers" \
    --header "authorization: Bearer ${AUTH0_MANAGEMENT_API_TOKEN}" | \
    jq -r '.[] | select(.is_system == false) | "Name: \(.name)\nIdentifier: \(.identifier)\nID: \(.id)\n"'

# Clients (Applications)
echo "📱 APPLICATIONS (Clients)"
echo "-------------------------"
curl -s --request GET \
    --url "${API_URL}/clients?fields=client_id,name,app_type&include_fields=true" \
    --header "authorization: Bearer ${AUTH0_MANAGEMENT_API_TOKEN}" | \
    jq -r '.[] | select(.name != "All Applications" and .name != "Default App") | "Name: \(.name)\nType: \(.app_type)\nClient ID: \(.client_id)\n"'

# Roles
echo "👥 ROLES"
echo "--------"
curl -s --request GET \
    --url "${API_URL}/roles" \
    --header "authorization: Bearer ${AUTH0_MANAGEMENT_API_TOKEN}" | \
    jq -r '.[] | "Name: \(.name)\nDescription: \(.description)\nID: \(.id)\n"'

# Actions
echo "⚡ ACTIONS"
echo "---------"
curl -s --request GET \
    --url "${API_URL}/actions/actions" \
    --header "authorization: Bearer ${AUTH0_MANAGEMENT_API_TOKEN}" | \
    jq -r '.actions[] | "Name: \(.name)\nTrigger: \(.supported_triggers[0].id)\nID: \(.id)\n"'

echo ""
echo "=========================================="
echo "✅ Fetch complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Use these IDs to fill in terraform/common/auth0.tf"
echo "2. Run terraform/common/scripts/import-auth0.sh"
echo "3. Run terraform plan to verify"

