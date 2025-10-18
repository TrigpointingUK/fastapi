/**
 * Auth0 Post User Registration Action for T:UK (trigpointing.uk)
 * 
 * This Action is triggered after a user successfully registers via Auth0.
 * It provisions the user in the FastAPI/MySQL database via webhook.
 * 
 * Flow:
 * 1. Generate nickname from email prefix
 * 2. Try to create user via POST /v1/users
 * 3. On username collision (409), retry with random 6-digit suffix
 * 4. Up to 10 retries with different random suffixes
 * 5. Set final nickname in Auth0 user metadata
 * 
 * Environment Variables (from Secrets):
 * - FASTAPI_URL: Base URL of FastAPI (e.g., https://api.trigpointing.uk)
 * - M2M_TOKEN: Machine-to-Machine token for webhook authentication
 */

exports.onExecutePostUserRegistration = async (event, api) => {
  const axios = require('axios');
  
  // Generate base nickname from email prefix
  // Auth0 signup only collects email/password by default
  // Nickname allows spaces and special characters (unlike username)
  const baseNickname = event.user.nickname || event.user.email.split('@')[0];
  
  // Try to create user, handling username collisions with random suffixes
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
            'Authorization': `Bearer ${event.secrets.M2M_TOKEN}`,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        }
      );
      
      console.log('User provisioned successfully:', event.user.user_id, 'with nickname:', nickname);
      
      // Set the final nickname in Auth0 user metadata
      api.user.setUserMetadata('nickname', nickname);
      return; // Success!
      
    } catch (error) {
      if (error.response?.status === 409 && 
          error.response?.data?.detail?.toLowerCase().includes('username')) {
        // Username collision - generate random 6-digit suffix
        // This avoids predictable patterns and potential DoS attacks
        const randomSuffix = Math.floor(100000 + Math.random() * 900000);
        nickname = `${baseNickname}${randomSuffix}`;
        attempt++;
        console.log(`Username collision on attempt ${attempt}, trying: ${nickname}`);
      } else {
        // Other error - log but don't fail registration
        console.error('User provisioning failed:', error.response?.data || error.message);
        console.error('User registered in Auth0 but not in database. Manual sync may be required.');
        return;
      }
    }
  }
  
  console.error('Failed to find unique username after', maxAttempts, 'attempts for user:', event.user.user_id);
  console.error('User registered in Auth0 but not in database. Manual provisioning required.');
};

