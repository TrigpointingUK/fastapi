import { useAuth0 } from "@auth0/auth0-react";
import { Link } from "react-router-dom";

export default function Home() {
  const { isAuthenticated, isLoading, user, error, loginWithRedirect } = useAuth0();

  if (error) {
    return (
      <div>
        <h1>Trigpointing UK</h1>
        <div style={{ color: 'red', padding: '1rem', backgroundColor: '#ffeeee', borderRadius: '4px' }}>
          <h2>Authentication Error</h2>
          <p><strong>Error:</strong> {error.message}</p>
          <button onClick={() => window.location.href = '/'}>Return to Home</button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div>
        <h1>Trigpointing UK</h1>
        <p>Authenticating...</p>
        <p style={{ fontSize: '0.9rem', color: '#666' }}>
          (If this takes more than a few seconds, check the browser console for errors)
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>Trigpointing UK</h1>
      {isAuthenticated && user ? (
        <div>
          <h2>Welcome back, {user.name || user.email}!</h2>
          <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
            {user.picture && (
              <img 
                src={user.picture} 
                alt={user.name || 'User avatar'} 
                style={{ 
                  width: '80px', 
                  height: '80px', 
                  borderRadius: '50%',
                  marginBottom: '1rem',
                  border: '2px solid #ddd'
                }}
              />
            )}
            <div style={{ marginTop: '1rem' }}>
              <p><strong>Email:</strong> {user.email}</p>
              {user.email_verified !== undefined && (
                <p>
                  <strong>Status:</strong>{' '}
                  <span style={{ color: user.email_verified ? 'green' : 'orange' }}>
                    {user.email_verified ? '✓ Verified' : '⚠ Not verified'}
                  </span>
                </p>
              )}
            </div>
          </div>
          
          <div style={{ 
            marginTop: '2rem', 
            padding: '1.5rem', 
            backgroundColor: '#f5f5f5',
            borderRadius: '8px'
          }}>
            <h3>Quick Links</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li style={{ marginBottom: '0.5rem' }}>
                <Link to="/app/12345" style={{ color: '#0066cc', textDecoration: 'none' }}>
                  📍 View example trig point (#12345)
                </Link>
              </li>
              <li style={{ marginBottom: '0.5rem' }}>
                <a href="https://api.trigpointing.me/docs" target="_blank" rel="noopener noreferrer" 
                   style={{ color: '#0066cc', textDecoration: 'none' }}>
                  📚 API Documentation
                </a>
              </li>
            </ul>
          </div>

          <div style={{ marginTop: '2rem', fontSize: '0.9rem', color: '#666' }}>
            <p>
              This is the new Trigpointing UK single-page application. More features coming soon!
            </p>
          </div>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            Welcome to the Trigpointing UK web application.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            This is a modern single-page application that will gradually replace
            legacy pages from the original website.
          </p>
          <p style={{ marginTop: '1.5rem' }}>
            <button 
              onClick={() => loginWithRedirect()}
              style={{
                padding: '0.75rem 1.5rem',
                fontSize: '1rem',
                cursor: 'pointer',
                backgroundColor: '#0066cc',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}
            >
              🔐 Login to continue
            </button>
          </p>
        </div>
      )}
    </div>
  );
}

