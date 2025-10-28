import { useAuth0 } from "@auth0/auth0-react";

export default function Home() {
  const { isAuthenticated, isLoading, user, loginWithRedirect } = useAuth0();

  if (isLoading) {
    return (
      <div>
        <h1>Trigpointing UK</h1>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Trigpointing UK</h1>
      {isAuthenticated && user ? (
        <div>
          <h2>Welcome, {user.name || user.email}!</h2>
          <div style={{ marginTop: '1rem' }}>
            <p><strong>Email:</strong> {user.email}</p>
            {user.email_verified !== undefined && (
              <p><strong>Email Verified:</strong> {user.email_verified ? 'Yes' : 'No'}</p>
            )}
            {user.picture && (
              <img 
                src={user.picture} 
                alt={user.name || 'User avatar'} 
                style={{ width: '64px', height: '64px', borderRadius: '50%', marginTop: '1rem' }}
              />
            )}
          </div>
        </div>
      ) : (
        <div>
          <p>Welcome to the Trigpointing UK web application.</p>
          <p>
            This is a modern single-page application that will gradually replace
            legacy pages from the original website.
          </p>
          <p style={{ marginTop: '1.5rem' }}>
            <button onClick={() => loginWithRedirect()}>
              Login to continue
            </button>
          </p>
        </div>
      )}
    </div>
  );
}

