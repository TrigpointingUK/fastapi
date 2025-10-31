import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import PhotoAlbum from './PhotoAlbum';
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
  const queryClient = useQueryClient();

  // Get all photos from the cache to find the requested photo
  const photoData = queryClient.getQueryData<{
    pages: PhotosResponse[];
    pageParams: number[];
  }>(['photos', 'infinite', 'unseen']) || queryClient.getQueryData<{
    pages: PhotosResponse[];
    pageParams: number[];
  }>(['photos', 'infinite', 'all']);

  const allPhotos = photoData?.pages.flatMap((page) => page.items) || [];
  const photoIdNum = photo_id ? parseInt(photo_id, 10) : null;
  const photoIndex = allPhotos.findIndex((p) => p.id === photoIdNum);

  // Navigate back to grid on close
  const handleClose = () => {
    navigate('/photos', { replace: false });
  };

  // If photo is found, open PhotoSwipe
  usePhotoSwipe({
    photos: photoIndex >= 0 ? [allPhotos[photoIndex]] : [], // Only show the single photo (requirement 1b)
    initialIndex: 0,
    onClose: handleClose,
  });

  // If photo not found or invalid ID, redirect to grid
  useEffect(() => {
    if (photoIdNum === null || photoIndex === -1) {
      if (allPhotos.length > 0) {
        // Photos are loaded but this photo isn't in the list
        navigate('/photos', { replace: true });
      }
      // Otherwise wait for photos to load
    }
  }, [photoIdNum, photoIndex, allPhotos.length, navigate]);

  // Render the PhotoAlbum grid in the background for the zoom animation
  return <PhotoAlbum />;
}

