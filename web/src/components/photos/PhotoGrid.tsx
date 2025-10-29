import PhotoThumbnail from "./PhotoThumbnail";

interface Photo {
  id: number;
  icon_url: string;
  photo_url: string;
  caption: string;
}

interface PhotoGridProps {
  photos: Photo[];
  onPhotoClick?: (photo: Photo) => void;
}

export default function PhotoGrid({ photos, onPhotoClick }: PhotoGridProps) {
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
        />
      ))}
    </div>
  );
}

