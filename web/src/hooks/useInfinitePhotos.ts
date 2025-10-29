import { useInfiniteQuery } from "@tanstack/react-query";

interface Photo {
  id: number;
  log_id: number;
  user_id: number;
  icon_url: string;
  photo_url: string;
  caption: string;
}

interface PhotosResponse {
  items: Photo[];
  total: number;
  pagination: {
    has_more: boolean;
    next_offset: number | null;
  };
}

export function useInfinitePhotos() {
  return useInfiniteQuery<PhotosResponse>({
    queryKey: ["photos", "infinite"],
    queryFn: async ({ pageParam = 0 }) => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      const response = await fetch(
        `${apiBase}/v1/photos?limit=24&skip=${pageParam}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch photos");
      }
      const data = await response.json();
      
      // Transform response to match expected format
      return {
        items: data.items || [],
        total: data.total || 0,
        pagination: {
          has_more: data.pagination?.has_more || false,
          next_offset: data.pagination?.has_more 
            ? (pageParam as number) + 24 
            : null,
        },
      };
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.pagination.next_offset,
  });
}

