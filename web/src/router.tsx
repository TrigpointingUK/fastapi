import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider, Link, Outlet } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";

const Home = lazy(() => import("./routes/Home"));
const NotFound = lazy(() => import("./routes/NotFound"));

function Shell() {
  const { isAuthenticated, loginWithRedirect, logout, user } = useAuth0();
  
  return (
    <>
      <nav className="nav">
        <Link to="/">Home</Link>
        {isAuthenticated ? (
          <>
            <span>Welcome, {user?.name}</span>
            <button onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}>
              Logout
            </button>
          </>
        ) : (
          <button onClick={() => loginWithRedirect()}>Login</button>
        )}
      </nav>
      <main className="container">
        <Suspense fallback={<div className="loading">Loading…</div>}>
          <Outlet />
        </Suspense>
      </main>
    </>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Shell />,
    children: [
      { index: true, element: <Home /> },
      { path: "*", element: <NotFound /> },
    ],
  },
], {
  basename: import.meta.env.BASE_URL,
});

export default function AppRouter() {
  return <RouterProvider router={router} />;
}

