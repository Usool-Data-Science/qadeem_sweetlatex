import { Navigate, useLocation } from "react-router-dom";
import { useSelector } from "react-redux";
import { useRetrieveUserQuery } from "../redux/features/auth/authApiSlice";

const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useSelector((state) => state.auth);

  // ── Skip the /users/me/ query entirely when we know the user is logged out.
  // Without `skip`, every page load fires a GET /users/me/ → 401 → refresh
  // attempt → second 401, polluting the console and creating unnecessary
  // network traffic. With `skip: !isAuthenticated`, the query is dormant
  // until the user has a valid session (isAuthenticated=true in Redux).
  const { data: user, isLoading } = useRetrieveUserQuery(undefined, {
    skip: !isAuthenticated,
  });

  const location = useLocation();

  // Still loading the user profile (only runs when isAuthenticated=true)
  if (isAuthenticated && isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="loading loading-ring loading-lg" />
      </div>
    );
  }

  // Authenticated and user data confirmed — render the protected page
  if (isAuthenticated && user) {
    return children;
  }

  // Not authenticated — redirect to login, preserving the intended URL
  // so after login the user returns to where they were trying to go
  const intendedUrl = location.pathname + location.search + location.hash;
  return <Navigate to="/login" state={{ next: intendedUrl }} replace />;
};

export default PrivateRoute;
