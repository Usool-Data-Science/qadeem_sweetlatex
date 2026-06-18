import { Navigate, useLocation } from "react-router-dom";
import { useSelector } from "react-redux";
import { useRetrieveUserQuery } from "../redux/features/auth/authApiSlice";

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useSelector((state) => state.auth);
  const location = useLocation();

  const { data: user, isLoading } = useRetrieveUserQuery(undefined, {
    skip: !isAuthenticated,
  });

  if (isAuthenticated && isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="loading loading-ring loading-lg" />
      </div>
    );
  }

  if (isAuthenticated && user) {
    const nextPage = location.state?.next || "/home";
    return <Navigate to={nextPage} replace />;
  }

  return children;
};

export default PublicRoute;
