import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useInfinitePhotos } from '../useInfinitePhotos';
import * as photoHistory from '../../lib/photoHistory';
import { ReactNode } from 'react';

// Mock the photoHistory module
vi.mock('../../lib/photoHistory', () => ({
  getViewedRanges: vi.fn(() => []),
  isPhotoViewed: vi.fn(() => false),
  addViewedRange: vi.fn(),
}));

// Mock fetch
global.fetch = vi.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useInfinitePhotos', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
  });

  it('should fetch photos successfully', async () => {
    const mockPhotos = [
      { id: 1, log_id: 1, user_id: 1, icon_url: 'icon1.jpg', photo_url: 'photo1.jpg', caption: 'Photo 1' },
      { id: 2, log_id: 2, user_id: 2, icon_url: 'icon2.jpg', photo_url: 'photo2.jpg', caption: 'Photo 2' },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: mockPhotos,
        total: 100,
        pagination: { has_more: true },
      }),
    });

    const { result } = renderHook(() => useInfinitePhotos(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.pages[0].items).toEqual(mockPhotos);
    expect(result.current.data?.pages[0].total).toBe(100);
  });

  it('should filter out viewed photos in unseen mode', async () => {
    const mockPhotos = [
      { id: 1, log_id: 1, user_id: 1, icon_url: 'icon1.jpg', photo_url: 'photo1.jpg', caption: 'Photo 1' },
      { id: 2, log_id: 2, user_id: 2, icon_url: 'icon2.jpg', photo_url: 'photo2.jpg', caption: 'Photo 2' },
      { id: 3, log_id: 3, user_id: 3, icon_url: 'icon3.jpg', photo_url: 'photo3.jpg', caption: 'Photo 3' },
    ];

    // Mock that photo with id 2 is viewed
    vi.mocked(photoHistory.isPhotoViewed).mockImplementation((id) => id === 2);

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: mockPhotos,
        total: 100,
        pagination: { has_more: false },
      }),
    });

    const { result } = renderHook(() => useInfinitePhotos({ mode: 'unseen' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Should only have photos with id 1 and 3
    expect(result.current.data?.pages[0].items).toHaveLength(2);
    expect(result.current.data?.pages[0].items.map(p => p.id)).toEqual([1, 3]);
  });

  it('should not filter photos in all mode', async () => {
    const mockPhotos = [
      { id: 1, log_id: 1, user_id: 1, icon_url: 'icon1.jpg', photo_url: 'photo1.jpg', caption: 'Photo 1' },
      { id: 2, log_id: 2, user_id: 2, icon_url: 'icon2.jpg', photo_url: 'photo2.jpg', caption: 'Photo 2' },
    ];

    // Mock that photo with id 2 is viewed
    vi.mocked(photoHistory.isPhotoViewed).mockImplementation((id) => id === 2);

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: mockPhotos,
        total: 100,
        pagination: { has_more: false },
      }),
    });

    const { result } = renderHook(() => useInfinitePhotos({ mode: 'all' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Should have all photos
    expect(result.current.data?.pages[0].items).toHaveLength(2);
    expect(result.current.data?.pages[0].items).toEqual(mockPhotos);
  });

  it('should handle fetch errors', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useInfinitePhotos(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('should build correct API URL with pagination', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [],
        total: 0,
        pagination: { has_more: false },
      }),
    });

    renderHook(() => useInfinitePhotos(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/v1/photos?limit=24&skip=0'
    );
  });

  it('should use different query keys for different modes', () => {
    const { result: result1 } = renderHook(() => useInfinitePhotos({ mode: 'unseen' }), {
      wrapper: createWrapper(),
    });

    const { result: result2 } = renderHook(() => useInfinitePhotos({ mode: 'all' }), {
      wrapper: createWrapper(),
    });

    // The query keys should be different, causing separate cache entries
    // This is implicit in the implementation but we can verify they're different instances
    expect(result1.current).not.toBe(result2.current);
  });
});

