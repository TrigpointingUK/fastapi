import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import Layout from '../components/layout/Layout';
import Spinner from '../components/ui/Spinner';
import { usePhotoSwipe } from '../hooks/usePhotoSwipe';
import { Photo } from '../lib/api';
import 'photoswipe/style.css';
import '../components/photos/photoswipe-custom.css';

interface PhotosResponse {
  items: Photo[];
  total: number;
  pagination: {
    has_more: boolean;
    next_offset: number | null;
  };
}

export default function PhotoDetail() {
  const { photo_id } = useParams<{ photo_id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const photoIdNum = photo_id ? parseInt(photo_id, 10) : null;
  const [photoForViewer, setPhotoForViewer] = useState<Photo | null>(null);

  // Check if photo was passed via router state (from log cards)
  const photoFromState = location.state?.photo as Photo | undefined;

  // Try to get photo from the photos grid cache
  const photoData = queryClient.getQueryData<{
    pages: PhotosResponse[];
    pageParams: number[];
  }>(['photos', 'infinite', 'unseen']) || queryClient.getQueryData<{
    pages: PhotosResponse[];
    pageParams: number[];
  }>(['photos', 'infinite', 'all']);

  const allPhotos = photoData?.pages.flatMap((page) => page.items) || [];
  const cachedPhoto = allPhotos.find((p) => p.id === photoIdNum);

  // Only fetch if we don't have the photo from state or cache
  const shouldFetch = !photoFromState && !cachedPhoto && photoIdNum !== null;

  // Fetch single photo by ID if not in cache or state
  const { data: fetchedPhoto, isLoading, error } = useQuery<Photo>({
    queryKey: ['photo', photoIdNum],
    queryFn: async () => {
      const apiBase = import.meta.env.VITE_API_BASE as string;
      const response = await fetch(`${apiBase}/v1/photos/${photoIdNum}`);
      if (!response.ok) {
        throw new Error('Failed to fetch photo');
      }
      return response.json();
    },
    enabled: shouldFetch,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Set the photo to display once we have it (from state, cache, or API)
  useEffect(() => {
    if (photoFromState) {
      setPhotoForViewer(photoFromState);
    } else if (cachedPhoto) {
      setPhotoForViewer(cachedPhoto);
    } else if (fetchedPhoto) {
      setPhotoForViewer(fetchedPhoto);
    }
  }, [photoFromState, cachedPhoto, fetchedPhoto]);

  // Navigate back to previous page on close
  const handleClose = () => {
    navigate(-1); // Go back in browser history
  };

  // Open PhotoSwipe when we have a photo
  usePhotoSwipe({
    photos: photoForViewer ? [photoForViewer] : [],
    initialIndex: 0,
    onClose: handleClose,
  });

  // Show loading state while fetching
  if (isLoading && !cachedPhoto && !photoFromState) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <Spinner size="lg" />
            <p className="mt-4 text-gray-600">Loading photo...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Show error state or photo not found
  if ((error || (!photoForViewer && !isLoading)) && !cachedPhoto && !photoFromState) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600 mb-4">
              {error ? 'Failed to load photo.' : 'Photo not found.'}
            </p>
            <button
              onClick={() => navigate('/photos')}
              className="px-4 py-2 bg-trig-green-600 text-white rounded hover:bg-trig-green-700"
            >
              Back to Photos
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  // Render empty layout as background (PhotoSwipe will overlay)
  return (
    <Layout>
      <div className="max-w-7xl mx-auto" />
    </Layout>
  );
}

