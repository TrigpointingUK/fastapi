import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Spinner from "./components/ui/Spinner";

const Home = lazy(() => import("./routes/Home"));
const PhotoAlbum = lazy(() => import("./routes/PhotoAlbum"));
const PhotoDetail = lazy(() => import("./routes/PhotoDetail"));
const UserProfile = lazy(() => import("./routes/UserProfile"));
const About = lazy(() => import("./routes/About"));
const AppDetail = lazy(() => import("./routes/AppDetail"));
const NotFound = lazy(() => import("./routes/NotFound"));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <Home />
        </Suspense>
      ),
    },
    {
      path: "/photos",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <PhotoAlbum />
        </Suspense>
      ),
    },
    {
      path: "/photos/:photo_id",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <PhotoDetail />
        </Suspense>
      ),
    },
    {
      path: "/profile/:userId",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <UserProfile />
        </Suspense>
      ),
    },
    {
      path: "/profile",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <UserProfile />
        </Suspense>
      ),
    },
    {
      path: "/about",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <About />
        </Suspense>
      ),
    },
    {
      path: "/app/:id",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <AppDetail />
        </Suspense>
      ),
    },
    {
      path: "*",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <NotFound />
        </Suspense>
      ),
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  }
);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
