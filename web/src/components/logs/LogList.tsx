import LogCard from "./LogCard";
import Spinner from "../ui/Spinner";

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

interface LogListProps {
  logs: Log[];
  isLoading?: boolean;
  emptyMessage?: string;
  onPhotoUpdate?: () => void;
}

export default function LogList({
  logs,
  isLoading = false,
  emptyMessage = "No logs found",
  onPhotoUpdate,
}: LogListProps) {
  if (isLoading) {
    return (
      <div className="py-12">
        <Spinner size="lg" />
        <p className="text-center text-gray-600 mt-4">Loading logs...</p>
      </div>
    );
  }

  if (!logs || logs.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {logs.map((log) => (
        <LogCard key={log.id} log={log} onPhotoUpdate={onPhotoUpdate} />
      ))}
    </div>
  );
}

