import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Spinner from "./components/ui/Spinner";
// NotFound is eagerly loaded to ensure it's always available, even if there are deployment issues
import NotFound from "./routes/NotFound";

const Home = lazy(() => import("./routes/Home"));
const PhotoAlbum = lazy(() => import("./routes/PhotoAlbum"));
const PhotoDetail = lazy(() => import("./routes/PhotoDetail"));
const TrigDetail = lazy(() => import("./routes/TrigDetail"));
const LogDetail = lazy(() => import("./routes/LogDetail"));
const UserProfile = lazy(() => import("./routes/UserProfile"));
const UserLogs = lazy(() => import("./routes/UserLogs"));
const UserPhotos = lazy(() => import("./routes/UserPhotos"));
const About = lazy(() => import("./routes/About"));
const AppDetail = lazy(() => import("./routes/AppDetail"));

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
      path: "/trig/:trigId",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <TrigDetail />
        </Suspense>
      ),
    },
    {
      path: "/logs/:logId",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <LogDetail />
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
      path: "/profile/:userId/logs",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <UserLogs />
        </Suspense>
      ),
    },
    {
      path: "/profile/:userId/photos",
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <UserPhotos />
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
      element: <NotFound />,
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  }
);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
