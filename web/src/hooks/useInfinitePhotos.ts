import { useInfiniteQuery } from "@tanstack/react-query";
import { getViewedRanges, isPhotoViewed, addViewedRange } from "../lib/photoHistory";
import { useEffect, useRef } from "react";

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

export type PhotoViewMode = 'unseen' | 'all';

interface UseInfinitePhotosOptions {
  mode?: PhotoViewMode;
}

export function useInfinitePhotos(options: UseInfinitePhotosOptions = {}) {
  const { mode = 'unseen' } = options;
  const lastBatchRef = useRef<{ min: number; max: number } | null>(null);

  const query = useInfiniteQuery<PhotosResponse>({
    queryKey: ["photos", "infinite", mode],
    queryFn: async ({ pageParam = 0 }) => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      const response = await fetch(
        `${apiBase}/v1/photos?limit=24&skip=${pageParam}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch photos");
      }
      const data = await response.json();
      
      let items = data.items || [];
      
      // Filter out viewed photos if in 'unseen' mode
      // Get fresh ranges each time to account for cleared history
      if (mode === 'unseen') {
        const viewedRanges = getViewedRanges();
        items = items.filter((photo: Photo) => 
          !isPhotoViewed(photo.id, viewedRanges)
        );
      }

      // Track the range of photos in this batch (before filtering)
      const originalItems = data.items || [];
      if (originalItems.length > 0) {
        const photoIds = originalItems.map((p: Photo) => p.id);
        const min = Math.min(...photoIds);
        const max = Math.max(...photoIds);
        lastBatchRef.current = { min, max };
      }
      
      // Transform response to match expected format
      return {
        items,
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

  // Update viewing history when photos are fetched
  useEffect(() => {
    if (query.data && lastBatchRef.current && mode === 'unseen') {
      const { min, max } = lastBatchRef.current;
      // Only mark as viewed if the range is reasonable (not marking entire database)
      const rangeSize = max - min + 1;
      if (rangeSize > 0 && rangeSize <= 100) {
        // Add the range to history after a short delay (user has seen them)
        const timeoutId = setTimeout(() => {
          addViewedRange(min, max);
        }, 2000); // Mark as viewed after 2 seconds
        
        return () => clearTimeout(timeoutId);
      } else {
        console.warn(`Skipping invalid photo range: ${min}-${max} (size: ${rangeSize})`);
      }
    }
  }, [query.data, mode]);

  return query;
}

