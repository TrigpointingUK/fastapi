import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Auth0Provider } from "@auth0/auth0-react";
import AppRouter from "./router";
import "./app.css";

const queryClient = new QueryClient();

const domain = import.meta.env.VITE_AUTH0_DOMAIN as string;
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID as string;
const audience = import.meta.env.VITE_AUTH0_AUDIENCE as string;

// Use the same base URL logic as vite.config.ts
// Local dev and staging: / (root)
// Production: /app/
const baseUrl = import.meta.env.BASE_URL || '/';
const redirectUri = window.location.origin + baseUrl;

// Debug logging for development
console.log('Auth0 Configuration:', {
  domain,
  clientId,
  audience,
  redirectUri,
  baseUrl,
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        audience,
        redirect_uri: redirectUri,
        scope: "openid profile email api:write api:read-pii",
      }}
      useRefreshTokens
      cacheLocation="localstorage"
      onRedirectCallback={(appState) => {
        console.log('Auth0 redirect callback:', appState);
      }}
    >
      <QueryClientProvider client={queryClient}>
        <AppRouter />
      </QueryClientProvider>
    </Auth0Provider>
  </React.StrictMode>
);

