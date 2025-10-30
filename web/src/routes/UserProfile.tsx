import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth0 } from "@auth0/auth0-react";
import Layout from "../components/layout/Layout";
import Card from "../components/ui/Card";
import Spinner from "../components/ui/Spinner";
import EditableField from "../components/ui/EditableField";
import { useUserProfile, updateUserProfile } from "../hooks/useUserProfile";

export default function UserProfile() {
  const { userId } = useParams<{ userId: string }>();
  const queryClient = useQueryClient();
  const { getAccessTokenSilently, user: authUser } = useAuth0();
  
  // If no userId in URL, fetch "me", otherwise fetch the specified user
  const targetUserId = userId || "me";
  const { data: user, isLoading, error } = useUserProfile(targetUserId);

  // Own profile if: no userId param, or userId matches the logged-in user's ID
  const isOwnProfile = !userId || (authUser && userId === authUser.sub);

  const handleFieldUpdate = async (field: string, value: string) => {
    try {
      // If updating full name, split into firstname and surname
      if (field === "fullname") {
        const nameParts = value.trim().split(/\s+/);
        const firstname = nameParts[0] || "";
        const surname = nameParts.slice(1).join(" ") || "";
        await updateUserProfile({ firstname, surname }, getAccessTokenSilently);
      } else {
        await updateUserProfile({ [field]: value }, getAccessTokenSilently);
      }
      // Invalidate to refetch
      queryClient.invalidateQueries({ queryKey: ["user", "profile"] });
    } catch (error) {
      console.error(`Failed to update ${field}:`, error);
      throw error;
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <div className="py-12 text-center">
            <Spinner size="lg" />
            <p className="text-gray-600 mt-4">Loading profile...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !user) {
    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <Card>
            <div className="text-center py-12">
              <p className="text-red-600 text-lg">
                {error ? "Failed to load user profile" : "User not found"}
              </p>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  const memberSince = user.member_since
    ? new Date(user.member_since).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : "Unknown";

  const apiBase = import.meta.env.VITE_API_BASE as string;
  const displayUserId = userId || user.id;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Header Section */}
        <Card className="mb-6">
          <div className="flex items-start gap-6 flex-wrap lg:flex-nowrap">
            {/* Left side: User info and stats */}
            <div className="flex-1 min-w-0">
              <div className="mb-4">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                  {user.name}
                </h1>
                <p className="text-gray-600">
                  Member since {memberSince}
                </p>
              </div>
              
              {user.stats && (
                <div className="flex gap-8 text-center">
                  <div>
                    <div className="text-2xl font-bold text-trig-green-600">
                      {user.stats.total_trigs_logged.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Trigs Logged</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-trig-green-600">
                      {user.stats.total_logs.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Total Logs</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-trig-green-600">
                      {user.stats.total_photos.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Photos</div>
                  </div>
                </div>
              )}
            </div>

            {/* Right side: Map */}
            <div className="w-full lg:w-auto flex-shrink-0">
              <img 
                src={`${apiBase}/v1/users/${displayUserId}/map`}
                alt={`${user.name}'s trig map`}
                className="rounded-lg border border-gray-200 w-full lg:w-32 h-auto"
                loading="lazy"
              />
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <EditableField
              label="Username"
              value={user.name}
              onSave={(value) => handleFieldUpdate("name", value)}
              editable={isOwnProfile}
              maxLength={30}
            />
            {!userId && (
              <EditableField
                label="Email"
                value={user.email || ""}
                onSave={(value) => handleFieldUpdate("email", value)}
                editable={isOwnProfile}
                placeholder="your.email@example.com"
                type="email"
                maxLength={255}
              />
            )}
            {(user.homepage || isOwnProfile) && (
              <EditableField
                label="Homepage"
                value={user.homepage || ""}
                onSave={(value) => handleFieldUpdate("homepage", value)}
                editable={isOwnProfile}
                placeholder="https://example.com"
                maxLength={255}
              />
            )}
            {((user.firstname || user.surname) || isOwnProfile) && (
              <EditableField
                label="Full Name"
                value={[user.firstname, user.surname].filter(Boolean).join(" ")}
                onSave={(value) => handleFieldUpdate("fullname", value)}
                editable={isOwnProfile}
                placeholder="First Last"
                maxLength={61}
              />
            )}
          </div>

          {(user.about || isOwnProfile) && (
            <div className="mt-6 flex gap-6 flex-wrap lg:flex-nowrap">
              <div className="flex-1 min-w-0">
                <EditableField
                  label="About"
                  value={user.about}
                  onSave={(value) => handleFieldUpdate("about", value)}
                  editable={isOwnProfile}
                  multiline
                  placeholder="Tell us about yourself..."
                />
              </div>
              
              {/* Badge on the right side */}
              <div className="w-full lg:w-auto flex-shrink-0 flex items-start">
                <img 
                  src={`${apiBase}/v1/users/${displayUserId}/badge`}
                  alt={`${user.name}'s badge`}
                  className="rounded border border-gray-200 w-full lg:w-72 h-auto"
                  loading="lazy"
                />
              </div>
            </div>
          )}
        </Card>

        {/* Breakdown Section */}
        {user.breakdown && (
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Trig Statistics Breakdown
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* By Current Use */}
              <Card>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Current Use
                </h3>
                <div className="space-y-2">
                  {Object.entries(user.breakdown.by_current_use)
                    .sort(([, a], [, b]) => b - a)
                    .map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-700">{key}</span>
                        <span className="font-medium text-trig-green-600">
                          {value}
                        </span>
                      </div>
                    ))}
                  {Object.keys(user.breakdown.by_current_use).length === 0 && (
                    <p className="text-gray-400 text-sm italic">No data</p>
                  )}
                </div>
              </Card>

              {/* By Historic Use */}
              <Card>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Historic Use
                </h3>
                <div className="space-y-2">
                  {Object.entries(user.breakdown.by_historic_use)
                    .sort(([, a], [, b]) => b - a)
                    .map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-700">{key}</span>
                        <span className="font-medium text-trig-green-600">
                          {value}
                        </span>
                      </div>
                    ))}
                  {Object.keys(user.breakdown.by_historic_use).length === 0 && (
                    <p className="text-gray-400 text-sm italic">No data</p>
                  )}
                </div>
              </Card>

              {/* By Physical Type */}
              <Card>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Physical Type
                </h3>
                <div className="space-y-2">
                  {Object.entries(user.breakdown.by_physical_type)
                    .sort(([, a], [, b]) => b - a)
                    .map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-700">{key}</span>
                        <span className="font-medium text-trig-green-600">
                          {value}
                        </span>
                      </div>
                    ))}
                  {Object.keys(user.breakdown.by_physical_type).length === 0 && (
                    <p className="text-gray-400 text-sm italic">No data</p>
                  )}
                </div>
              </Card>

              {/* By Condition */}
              <Card>
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  Condition
                </h3>
                <div className="space-y-2">
                  {Object.entries(user.breakdown.by_condition)
                    .sort(([, a], [, b]) => b - a)
                    .map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-700">{key}</span>
                        <span className="font-medium text-trig-green-600">
                          {value}
                        </span>
                      </div>
                    ))}
                  {Object.keys(user.breakdown.by_condition).length === 0 && (
                    <p className="text-gray-400 text-sm italic">No data</p>
                  )}
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

