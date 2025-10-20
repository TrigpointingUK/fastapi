/**
 * Auth0 Post User Registration Action for ${environment}
 * 
 * This Action is triggered after a user successfully registers via Auth0.
 * It provisions the user in the FastAPI/MySQL database via webhook.
 * 
 * Flow:
 * 1. Obtain M2M token using client credentials (OAuth2 client_credentials flow)
 * 2. Generate nickname from email prefix
 * 3. Try to create user via POST /v1/users
 * 4. On username collision (409), retry with random 6-digit suffix
 * 5. Up to 10 retries with different random suffixes
 * 6. Set final nickname in Auth0 user metadata
 * 
 * Environment Variables (from Secrets):
 * - FASTAPI_URL: Base URL of FastAPI (e.g., https://api.trigpointing.me)
 * - M2M_CLIENT_ID: Auth0 M2M client ID
 * - M2M_CLIENT_SECRET: Auth0 M2M client secret
 * - AUTH0_DOMAIN: Auth0 tenant domain (e.g., trigpointing-me.eu.auth0.com)
 * - API_AUDIENCE: FastAPI API audience (e.g., https://api.trigpointing.me/)
 */

exports.onExecutePostUserRegistration = async (event, api) => {
  const axios = require('axios');
  
  // Step 1: Obtain M2M token using client credentials
  let m2mToken;
  try {
    const tokenResponse = await axios.post(
      `https://$${event.secrets.AUTH0_DOMAIN}/oauth/token`,
      {
        grant_type: 'client_credentials',
        client_id: event.secrets.M2M_CLIENT_ID,
        client_secret: event.secrets.M2M_CLIENT_SECRET,
        audience: event.secrets.API_AUDIENCE
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 5000
      }
    );
    m2mToken = tokenResponse.data.access_token;
  } catch (error) {
    console.error('[${environment}] Failed to obtain M2M token:', error.response?.data || error.message);
    console.error('[${environment}] User registered in Auth0 but not in database. M2M authentication failed.');
    return;
  }
  
  // Step 2: Generate base nickname from email prefix
  // Auth0 signup only collects email/password by default
  // Nickname allows spaces and special characters (unlike username)
  const baseNickname = event.user.nickname || event.user.email.split('@')[0];
  
  // Step 3-5: Try to create user, handling username collisions with random suffixes
  let nickname = baseNickname;
  let attempt = 0;
  const maxAttempts = 10;
  
  while (attempt < maxAttempts) {
    const payload = {
      username: nickname,  // Maps to user.name (nickname/display name)
      email: event.user.email,
      auth0_user_id: event.user.user_id
    };
    
    try {
      await axios.post(
        event.secrets.FASTAPI_URL + '/v1/users',
        payload,
        {
          headers: {
            'Authorization': `Bearer $${m2mToken}`,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        }
      );
      
      console.log('[${environment}] User provisioned successfully:', event.user.user_id, 'with nickname:', nickname);
      
      // Step 6: Set the final nickname in Auth0 user metadata
      api.user.setUserMetadata('nickname', nickname);
      return; // Success!
      
    } catch (error) {
      if (error.response?.status === 409 && 
          error.response?.data?.detail?.toLowerCase().includes('username')) {
        // Username collision - generate random 6-digit suffix
        // This avoids predictable patterns and potential DoS attacks
        const randomSuffix = Math.floor(100000 + Math.random() * 900000);
        nickname = `$${baseNickname}$${randomSuffix}`;
        attempt++;
        console.log(`[${environment}] Username collision on attempt $${attempt}, trying: $${nickname}`);
      } else {
        // Other error - log but don't fail registration
        console.error('[${environment}] User provisioning failed:', error.response?.data || error.message);
        console.error('[${environment}] User registered in Auth0 but not in database. Manual sync may be required.');
        return;
      }
    }
  }
  
  console.error('[${environment}] Failed to find unique username after', maxAttempts, 'attempts for user:', event.user.user_id);
  console.error('[${environment}] User registered in Auth0 but not in database. Manual provisioning required.');
};

