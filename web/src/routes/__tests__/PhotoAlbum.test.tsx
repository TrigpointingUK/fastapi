import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import PhotoAlbum from '../PhotoAlbum';
import * as photoHistory from '../../lib/photoHistory';

// Mock modules
vi.mock('../../lib/photoHistory', () => ({
  getViewedRanges: vi.fn(() => []),
  isPhotoViewed: vi.fn(() => false),
  addViewedRange: vi.fn(),
  clearHistory: vi.fn(),
  getHistoryStats: vi.fn(() => ({ rangeCount: 0, totalPhotosViewed: 0 })),
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
  
  return ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
  );
};

describe('PhotoAlbum Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(global.fetch).mockClear();
    localStorage.clear();
  });

  const mockPhotosResponse = {
    items: [
      { id: 1, log_id: 1, user_id: 1, icon_url: 'icon1.jpg', photo_url: 'photo1.jpg', caption: 'Photo 1' },
      { id: 2, log_id: 2, user_id: 2, icon_url: 'icon2.jpg', photo_url: 'photo2.jpg', caption: 'Photo 2' },
      { id: 3, log_id: 3, user_id: 3, icon_url: 'icon3.jpg', photo_url: 'photo3.jpg', caption: 'Photo 3' },
    ],
    total: 100,
    pagination: { has_more: true },
  };

  it('should render Photo Gallery heading', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    } as Response);

    render(<PhotoAlbum />, { wrapper: createWrapper() });
    expect(screen.getByText('Photo Gallery')).toBeInTheDocument();
  });

  it('should show loading state initially', () => {
    vi.mocked(global.fetch).mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<PhotoAlbum />, { wrapper: createWrapper() });
    // Use getAllByText since "Loading photos..." appears in both header and spinner
    expect(screen.getAllByText('Loading photos...').length).toBeGreaterThan(0);
  });

  it('should display photos after loading', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      const images = screen.getAllByRole('img');
      expect(images.length).toBeGreaterThan(0);
    });
  });

  it('should display photo count', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Showing 3 of 100 photos/)).toBeInTheDocument();
    });
  });

  it('should have Unseen Photos selected by default', () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });
    
    const unseenButton = screen.getByText('Unseen Photos');
    expect(unseenButton).toHaveClass('bg-white');
    expect(unseenButton).toHaveClass('text-trig-green-600');
  });

  it('should switch to All Photos mode when clicked', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    const allPhotosButton = screen.getByText('All Photos');
    fireEvent.click(allPhotosButton);

    await waitFor(() => {
      expect(allPhotosButton).toHaveClass('bg-white');
      expect(allPhotosButton).toHaveClass('text-trig-green-600');
    });
  });

  it('should show Reset History button when history exists', async () => {
    vi.mocked(photoHistory.getHistoryStats).mockReturnValue({
      rangeCount: 2,
      totalPhotosViewed: 50,
    });

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Reset History')).toBeInTheDocument();
    });
  });

  it('should not show Reset History button when no history', async () => {
    vi.mocked(photoHistory.getHistoryStats).mockReturnValue({
      rangeCount: 0,
      totalPhotosViewed: 0,
    });

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.queryByText('Reset History')).not.toBeInTheDocument();
    });
  });

  it('should show previously viewed count in unseen mode', async () => {
    vi.mocked(photoHistory.getHistoryStats).mockReturnValue({
      rangeCount: 2,
      totalPhotosViewed: 50,
    });

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/50 previously viewed/)).toBeInTheDocument();
    });
  });

  it('should display error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load photos/)).toBeInTheDocument();
    });
  });

  it('should show empty state when all photos are viewed (unseen mode)', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...mockPhotosResponse, items: [] }),
    });

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("You've seen all the photos!")).toBeInTheDocument();
    });
  });

  it('should call clearHistory when Reset History button is clicked and confirmed', async () => {
    vi.mocked(photoHistory.getHistoryStats).mockReturnValue({
      rangeCount: 2,
      totalPhotosViewed: 50,
    });

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Reset History')).toBeInTheDocument();
    });

    const resetButton = screen.getByText('Reset History');
    fireEvent.click(resetButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(photoHistory.clearHistory).toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('should not clear history when confirmation is cancelled', async () => {
    vi.mocked(photoHistory.getHistoryStats).mockReturnValue({
      rangeCount: 2,
      totalPhotosViewed: 50,
    });

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockPhotosResponse,
    });

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(<PhotoAlbum />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Reset History')).toBeInTheDocument();
    });

    const resetButton = screen.getByText('Reset History');
    fireEvent.click(resetButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(photoHistory.clearHistory).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });
});

