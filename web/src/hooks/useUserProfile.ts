import { useQuery } from "@tanstack/react-query";
import { useAuth0 } from "@auth0/auth0-react";

interface UserBreakdown {
  by_current_use: Record<string, number>;
  by_historic_use: Record<string, number>;
  by_physical_type: Record<string, number>;
  by_condition: Record<string, number>;
}

interface UserStats {
  total_logs: number;
  total_trigs_logged: number;
  total_photos: number;
}

export interface UserProfile {
  id: number;
  name: string;
  firstname: string;
  surname: string;
  email?: string;
  homepage: string | null;
  about: string;
  member_since: string | null;
  stats?: UserStats;
  breakdown?: UserBreakdown;
}

export function useUserProfile(userId: string | number) {
  const { getAccessTokenSilently, isAuthenticated, loginWithRedirect } = useAuth0();
  
  return useQuery<UserProfile>({
    queryKey: ["user", "profile", userId],
    queryFn: async () => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      
      // Get token if viewing own profile
      let headers: Record<string, string> = {};
      if (userId === "me") {
        if (!isAuthenticated) {
          throw new Error("Not authenticated - please log in");
        }
        
        try {
          const token = await getAccessTokenSilently({
            cacheMode: 'on', // Try to use cached token first
          });
          headers = { Authorization: `Bearer ${token}` };
        } catch (error) {
          console.error("Failed to get access token:", error);
          // If token retrieval fails, trigger re-login
          await loginWithRedirect({
            appState: { returnTo: window.location.pathname }
          });
          throw new Error("Token expired - redirecting to login");
        }
      }
      
      // Include prefs (email) when fetching own profile
      const includes = userId === "me" 
        ? "stats,breakdown,prefs" 
        : "stats,breakdown";
      
      const response = await fetch(
        `${apiBase}/v1/users/${userId}?include=${includes}`,
        { headers }
      );
      if (!response.ok) {
        throw new Error("Failed to fetch user profile");
      }
      return response.json();
    },
    retry: false, // Don't retry if token fails
  });
}

export async function updateUserProfile(
  fields: Partial<UserProfile>,
  getAccessToken: () => Promise<string>
): Promise<void> {
  const apiBase = import.meta.env.VITE_API_BASE as string;
  
  // Get the access token
  const token = await getAccessToken();
  
  const response = await fetch(`${apiBase}/v1/users/me`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(fields),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update profile");
  }
}

