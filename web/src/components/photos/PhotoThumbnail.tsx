import { useState } from "react";

interface PhotoThumbnailProps {
  id: number;
  iconUrl: string;
  photoUrl: string;
  caption: string;
  onClick?: () => void;
}

export default function PhotoThumbnail({
  photoUrl,
  caption,
  onClick,
}: PhotoThumbnailProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  return (
    <div
      className="relative group cursor-pointer overflow-hidden rounded-lg bg-gray-100"
      onClick={onClick}
    >
      {/* Loading Placeholder */}
      {!loaded && !error && (
        <div className="aspect-square flex items-center justify-center">
          <div className="h-8 w-8 border-2 border-trig-green-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="aspect-square flex items-center justify-center bg-gray-200">
          <span className="text-gray-400 text-sm">Failed to load</span>
        </div>
      )}

      {/* Image */}
      {!error && (
        <img
          src={photoUrl}
          alt={caption}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            loaded ? "opacity-100" : "opacity-0"
          } group-hover:scale-110 transition-transform duration-300`}
        />
      )}

      {/* Caption Overlay */}
      {loaded && !error && caption && (
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <p className="text-white text-xs truncate">{caption}</p>
        </div>
      )}
    </div>
  );
}

