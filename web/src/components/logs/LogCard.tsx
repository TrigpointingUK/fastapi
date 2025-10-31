import { Link } from "react-router-dom";
import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import toast from "react-hot-toast";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import StarRating from "../ui/StarRating";
import { rotatePhoto } from "../../lib/api";

interface Photo {
  id: number;
  icon_url: string;
  caption: string;
}

interface Log {
  id: number;
  trig_id: number;
  user_id: number;
  trig_name?: string;
  user_name?: string;
  date: string;
  time: string;
  condition: string;
  comment: string;
  score: number;
  photos?: Photo[];
}

interface LogCardProps {
  log: Log;
  // Deprecated: use log.trig_name and log.user_name instead
  userName?: string;
  trigName?: string;
  onPhotoUpdate?: () => void;
}

const conditionMap: Record<string, { label: string; variant: "good" | "damaged" | "missing" | "unknown" }> = {
  G: { label: "Good", variant: "good" },
  D: { label: "Damaged", variant: "damaged" },
  M: { label: "Missing", variant: "missing" },
  P: { label: "Possibly Missing", variant: "damaged" },
  U: { label: "Unknown", variant: "unknown" },
};

export default function LogCard({ log, userName, trigName, onPhotoUpdate }: LogCardProps) {
  const condition = conditionMap[log.condition] || conditionMap.U;
  const formattedDate = new Date(log.date).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  // Use denormalized fields if available, otherwise fall back to props
  const displayTrigName = log.trig_name || trigName;
  const displayUserName = log.user_name || userName;

  const { getAccessTokenSilently } = useAuth0();
  const [rotatingPhoto, setRotatingPhoto] = useState<number | null>(null);

  const handleRotate = async (photoId: number, angle: number, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();

    setRotatingPhoto(photoId);

    try {
      const token = await getAccessTokenSilently();
      await rotatePhoto(photoId, angle, token);
      
      toast.success("Photo rotated successfully");
      
      // Call the callback to refresh the photo data
      if (onPhotoUpdate) {
        onPhotoUpdate();
      }
    } catch (error) {
      console.error("Failed to rotate photo:", error);
      toast.error("Failed to rotate photo. Please try again.");
    } finally {
      setRotatingPhoto(null);
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <Link
              to={`/trig/${log.trig_id}`}
              className="text-lg font-semibold text-trig-green-600 hover:text-trig-green-700 hover:underline"
            >
              TP{log.trig_id}
              {displayTrigName && (
                <>
                  <span className="text-gray-400 mx-2">·</span>
                  <span className="font-normal text-gray-700">{displayTrigName}</span>
                </>
              )}
            </Link>
            <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
              <span>
                by{" "}
                {displayUserName ? (
                  <Link
                    to={`/profile/${log.user_id}`}
                    className="text-trig-green-600 hover:underline"
                  >
                    {displayUserName}
                  </Link>
                ) : (
                  <Link
                    to={`/profile/${log.user_id}`}
                    className="text-trig-green-600 hover:underline"
                  >
                    User #{log.user_id}
                  </Link>
                )}
              </span>
              <span className="text-gray-400">·</span>
              <Badge variant={condition.variant}>{condition.label}</Badge>
              <StarRating 
                rating={log.score / 2} 
                size="sm" 
                title={`${log.score}/10`}
              />
              <span className="text-gray-400">·</span>
              <span className="text-gray-700">{formattedDate}</span>
              <span className="text-gray-500 text-xs">{log.time}</span>
            </div>
          </div>
        </div>

        {/* Comment and Photos - Side by Side */}
        {(log.comment || (log.photos && log.photos.length > 0)) && (
          <div className="flex gap-4">
            {/* Comment - Left 33% */}
            <div className="flex-[2] min-w-0">
              {log.comment && (
                <p className="text-gray-700 text-sm leading-relaxed">{log.comment}</p>
              )}
            </div>

            {/* Photos - Right 66% */}
            {log.photos && log.photos.length > 0 && (
              <div className="flex-[1] flex gap-2 overflow-x-auto pb-2">
                {log.photos.slice(0, 6).map((photo) => (
                  <div
                    key={photo.id}
                    className="relative h-20 w-20 flex-shrink-0 group"
                  >
                    <img
                      src={photo.icon_url}
                      alt={photo.caption}
                      className="h-full w-full object-cover rounded border border-gray-200 cursor-pointer transition-all duration-200 group-hover:scale-110"
                      title={photo.caption}
                    />
                    {/* Rotation Controls - appear on hover */}
                    <div className="absolute inset-0 flex items-start justify-between p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <button
                        onClick={(e) => handleRotate(photo.id, -90, e)}
                        disabled={rotatingPhoto === photo.id}
                        className="bg-black/70 hover:bg-black/90 text-white rounded p-1.5 transition-colors disabled:opacity-50 shadow-lg relative z-20"
                        title="Rotate left 90°"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                          />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => handleRotate(photo.id, 90, e)}
                        disabled={rotatingPhoto === photo.id}
                        className="bg-black/70 hover:bg-black/90 text-white rounded p-1.5 transition-colors disabled:opacity-50 shadow-lg relative z-20"
                        title="Rotate right 90°"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
                {log.photos.length > 6 && (
                  <div className="h-20 w-20 flex items-center justify-center bg-gray-100 rounded border border-gray-200 flex-shrink-0 text-sm text-gray-600">
                    +{log.photos.length - 6}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
