import { useQuery } from "@tanstack/react-query";
import { Trig } from "../lib/api";

export function useTrigDetail(trigId: number) {
  return useQuery<Trig>({
    queryKey: ["trig", trigId, "details"],
    queryFn: async () => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      const response = await fetch(
        `${apiBase}/v1/trigs/${trigId}?include=details,stats`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch trig details");
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

