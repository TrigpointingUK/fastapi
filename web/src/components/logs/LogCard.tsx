import { Link } from "react-router-dom";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import StarRating from "../ui/StarRating";

interface Photo {
  id: number;
  icon_url: string;
  caption: string;
}

interface Log {
  id: number;
  trig_id: number;
  user_id: number;
  date: string;
  time: string;
  condition: string;
  comment: string;
  score: number;
  photos?: Photo[];
}

interface LogCardProps {
  log: Log;
  userName?: string;
  trigName?: string;
}

const conditionMap: Record<string, { label: string; variant: "good" | "damaged" | "missing" | "unknown" }> = {
  G: { label: "Good", variant: "good" },
  D: { label: "Damaged", variant: "damaged" },
  M: { label: "Missing", variant: "missing" },
  P: { label: "Possibly Missing", variant: "damaged" },
  U: { label: "Unknown", variant: "unknown" },
};

export default function LogCard({ log, userName, trigName }: LogCardProps) {
  const condition = conditionMap[log.condition] || conditionMap.U;
  const formattedDate = new Date(log.date).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

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
              {trigName || `TP${log.trig_id}`}
            </Link>
            <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
              <span>
                by{" "}
                <Link
                  to={`/user/${log.user_id}`}
                  className="text-trig-green-600 hover:underline"
                >
                  {userName || `User #${log.user_id}`}
                </Link>
              </span>
              <span className="text-gray-400">·</span>
              <Badge variant={condition.variant}>{condition.label}</Badge>
              <div className="flex items-center gap-1">
                <StarRating rating={log.score} size="sm" />
                <span className="text-sm text-gray-600">({log.score * 2}/10)</span>
              </div>
              <span className="text-gray-400">·</span>
              <span className="text-gray-700">{formattedDate}</span>
              <span className="text-gray-500 text-xs">{log.time}</span>
            </div>
          </div>
        </div>

        {/* Comment and Photos - Side by Side */}
        {(log.comment || (log.photos && log.photos.length > 0)) && (
          <div className="flex gap-4">
            {/* Comment - Left 50% */}
            <div className="flex-1 min-w-0">
              {log.comment && (
                <p className="text-gray-700 text-sm leading-relaxed">{log.comment}</p>
              )}
            </div>

            {/* Photos - Right 50% */}
            {log.photos && log.photos.length > 0 && (
              <div className="flex-1 flex gap-2 overflow-x-auto pb-2">
                {log.photos.slice(0, 6).map((photo) => (
                  <img
                    key={photo.id}
                    src={photo.icon_url}
                    alt={photo.caption}
                    className="h-20 w-20 object-cover rounded border border-gray-200 flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                    title={photo.caption}
                  />
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

