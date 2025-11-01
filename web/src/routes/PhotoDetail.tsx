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
  const [allPhotosForViewer, setAllPhotosForViewer] = useState<Photo[]>([]);
  const [initialPhotoIndex, setInitialPhotoIndex] = useState(0);

  // Check if photo was passed via router state (from log cards)
  const photoFromState = location.state?.photo as Photo | undefined;
  const allPhotosFromState = location.state?.allPhotos as Photo[] | undefined;
  const contextFromState = location.state?.context as string | undefined;

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
      
      // If we have all photos from a log context, set them up for navigation
      if (allPhotosFromState && allPhotosFromState.length > 0 && contextFromState === 'log') {
        setAllPhotosForViewer(allPhotosFromState);
        // Find the index of the clicked photo
        const index = allPhotosFromState.findIndex(p => p.id === photoFromState.id);
        setInitialPhotoIndex(index >= 0 ? index : 0);
      } else {
        // Single photo mode (non-log context)
        setAllPhotosForViewer([photoFromState]);
        setInitialPhotoIndex(0);
      }
    } else if (cachedPhoto) {
      setPhotoForViewer(cachedPhoto);
      setAllPhotosForViewer([cachedPhoto]);
      setInitialPhotoIndex(0);
    } else if (fetchedPhoto) {
      setPhotoForViewer(fetchedPhoto);
      setAllPhotosForViewer([fetchedPhoto]);
      setInitialPhotoIndex(0);
    }
  }, [photoFromState, cachedPhoto, fetchedPhoto, allPhotosFromState, contextFromState]);

  // Navigate back to previous page on close
  const handleClose = () => {
    navigate(-1); // Go back in browser history
  };

  // Handle photo rotation
  const handlePhotoRotated = (updatedPhoto: Photo) => {
    // Update the photo in the viewer state
    setPhotoForViewer(updatedPhoto);
    
    // Update the photo in the array
    setAllPhotosForViewer(prev => 
      prev.map(p => p.id === updatedPhoto.id ? updatedPhoto : p)
    );
    
    // Update the cache if this photo came from the photo grid
    const photoData = queryClient.getQueryData<{
      pages: PhotosResponse[];
      pageParams: number[];
    }>(['photos', 'infinite', 'unseen']) || queryClient.getQueryData<{
      pages: PhotosResponse[];
      pageParams: number[];
    }>(['photos', 'infinite', 'all']);
    
    if (photoData) {
      queryClient.setQueryData(['photos', 'infinite', 'unseen'], (oldData: { pages: PhotosResponse[]; pageParams: number[] } | undefined) => {
        if (!oldData?.pages) return oldData;
        return {
          ...oldData,
          pages: oldData.pages.map((page: PhotosResponse) => ({
            ...page,
            items: page.items.map((photo: Photo) =>
              photo.id === updatedPhoto.id ? updatedPhoto : photo
            ),
          })),
        };
      });
      
      queryClient.setQueryData(['photos', 'infinite', 'all'], (oldData: { pages: PhotosResponse[]; pageParams: number[] } | undefined) => {
        if (!oldData?.pages) return oldData;
        return {
          ...oldData,
          pages: oldData.pages.map((page: PhotosResponse) => ({
            ...page,
            items: page.items.map((photo: Photo) =>
              photo.id === updatedPhoto.id ? updatedPhoto : photo
            ),
          })),
        };
      });
    }
  };

  // Open PhotoSwipe when we have a photo
  usePhotoSwipe({
    photos: allPhotosForViewer,
    initialIndex: initialPhotoIndex,
    onClose: handleClose,
    onPhotoRotated: handlePhotoRotated,
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

