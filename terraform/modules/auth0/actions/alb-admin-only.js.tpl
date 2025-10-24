/**
 * Post-Login Action: Block Non-Admin Users from ALB OIDC
 * 
 * This action restricts access to the aws-alb application (used for
 * ALB OIDC authentication to cache.trigpointing.uk and phpmyadmin.trigpointing.uk)
 * to users with the api-admin role only.
 */

exports.onExecutePostLogin = async (event, api) => {
  const namespace = '${namespace}';
  
  // Only apply this restriction to the aws-alb application
  if (event.client.client_id !== '${alb_client_id}') {
    return;
  }
  
  // Get user roles from authorization context
  const roles = (event.authorization || {}).roles || [];
  
  // Check if user has api-admin role
  const isAdmin = roles.includes('api-admin');
  
  if (!isAdmin) {
    // Deny access with a clear error message
    api.access.deny('access_denied', 'Access to admin tools requires api-admin role.');
  }
};

