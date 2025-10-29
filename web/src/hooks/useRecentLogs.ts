import { useQuery } from "@tanstack/react-query";

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

interface LogsResponse {
  items: Log[];
  total: number;
  pagination: {
    has_more: boolean;
    next_link: string | null;
    prev_link: string | null;
  };
}

export function useRecentLogs(limit = 10) {
  return useQuery<LogsResponse>({
    queryKey: ["logs", "recent", limit],
    queryFn: async () => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      const response = await fetch(
        `${apiBase}/v1/logs?limit=${limit}&order=-upd_timestamp&include=photos`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch recent logs");
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

