import PhotoThumbnail from "./PhotoThumbnail";
import { Photo } from "../../lib/api";

interface PhotoGridProps {
  photos: Photo[];
  onPhotoClick?: (photo: Photo) => void;
  onPhotoRotated?: (updatedPhoto: Photo) => void;
}

export default function PhotoGrid({ photos, onPhotoClick, onPhotoRotated }: PhotoGridProps) {
  if (!photos || photos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No photos found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {photos.map((photo) => (
        <PhotoThumbnail
          key={photo.id}
          id={photo.id}
          iconUrl={photo.icon_url}
          photoUrl={photo.photo_url}
          caption={photo.caption}
          onClick={() => onPhotoClick?.(photo)}
          onPhotoRotated={onPhotoRotated}
        />
      ))}
    </div>
  );
}

