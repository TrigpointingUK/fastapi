import { useQuery } from "@tanstack/react-query";

interface NewsItem {
  id: number;
  date: string;
  title: string;
  summary: string;
  link?: string | null;
}

export function useNews() {
  return useQuery<NewsItem[]>({
    queryKey: ["news"],
    queryFn: async () => {
      const response = await fetch("/news.json");
      if (!response.ok) {
        throw new Error("Failed to fetch news");
      }
      return response.json();
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

