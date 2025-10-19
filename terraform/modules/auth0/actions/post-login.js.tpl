/**
 * Post-Login Action: Add Roles to Tokens
 * 
 * This action adds user roles to both the access token and ID token
 * as custom claims. This allows:
 * - Backend API to enforce role-based authorization
 * - Frontend to make UI decisions based on roles
 */

exports.onExecutePostLogin = async (event, api) => {
  const namespace = '${namespace}';
  const roles = (event.authorization || {}).roles || [];
  
  // Add roles to access token (for API authorization)
  api.accessToken.setCustomClaim(namespace + 'roles', roles);
  
  // Add roles to ID token (for frontend UI decisions)
  api.idToken.setCustomClaim(namespace + 'roles', roles);
};

