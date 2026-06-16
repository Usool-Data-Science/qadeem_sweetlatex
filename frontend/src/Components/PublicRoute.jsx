import { Navigate, useLocation } from "react-router-dom";
import { useSelector } from "react-redux";
import useAuth from "../hooks/use-auth";

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { user, loadingUser } = useAuth();
  const location = useLocation();

  if (loadingUser) {
    return <span className="loading loading-ring loading-lg"></span>;
  }

  if (user) {
    // Redirect to the intended page or default pages
    const nextPage =
      location.state?.next || (isAuthenticated ? "/home" : "/login");
    return <Navigate to={nextPage} replace />;
  }

  // Allow unauthenticated users to access the route
  return children;
};

export default PublicRoute;
