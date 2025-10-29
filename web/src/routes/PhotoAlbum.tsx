import { useEffect } from "react";
import { useInView } from "react-intersection-observer";
import Layout from "../components/layout/Layout";
import PhotoGrid from "../components/photos/PhotoGrid";
import Spinner from "../components/ui/Spinner";
import Button from "../components/ui/Button";
import { useInfinitePhotos } from "../hooks/useInfinitePhotos";

export default function PhotoAlbum() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    error,
  } = useInfinitePhotos();

  // Intersection observer to trigger loading more photos
  const { ref: loadMoreRef, inView } = useInView({
    threshold: 0,
    rootMargin: "200px", // Start loading 200px before reaching the trigger
  });

  // Auto-fetch when scrolling into view
  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Flatten all pages into a single array
  const allPhotos = data?.pages.flatMap((page) => page.items) || [];
  const totalPhotos = data?.pages[0]?.total || 0;

  if (error) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">Photo Gallery</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600 mb-4">
              Failed to load photos. Please try again later.
            </p>
            <Button onClick={() => window.location.reload()}>Reload Page</Button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Photo Gallery</h1>
          <p className="text-gray-600">
            {isLoading ? (
              "Loading photos..."
            ) : (
              <>
                Showing {allPhotos.length.toLocaleString()} of{" "}
                {totalPhotos.toLocaleString()} photos
              </>
            )}
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="py-12">
            <Spinner size="lg" />
            <p className="text-center text-gray-600 mt-4">Loading photos...</p>
          </div>
        )}

        {/* Photo Grid */}
        {!isLoading && allPhotos.length > 0 && (
          <>
            <PhotoGrid
              photos={allPhotos}
              onPhotoClick={(photo) => {
                // Future: Open lightbox/modal
                console.log("Photo clicked:", photo);
              }}
            />

            {/* Load More Trigger */}
            <div ref={loadMoreRef} className="py-8 text-center">
              {isFetchingNextPage && (
                <>
                  <Spinner size="md" />
                  <p className="text-gray-600 mt-4">Loading more photos...</p>
                </>
              )}
              {!hasNextPage && allPhotos.length > 0 && (
                <p className="text-gray-500">
                  You've reached the end! All {allPhotos.length.toLocaleString()}{" "}
                  photos loaded.
                </p>
              )}
            </div>
          </>
        )}

        {/* Empty State */}
        {!isLoading && allPhotos.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📷</div>
            <p className="text-gray-600 text-lg">No photos found</p>
          </div>
        )}
      </div>
    </Layout>
  );
}

