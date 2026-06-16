import { Navigate, useLocation } from "react-router-dom";
import { useRetrieveUserQuery } from "../redux/features/auth/authApiSlice";

const PrivateRoute = ({ children }) => {
  const { data: user, isLoading: loadingUser } = useRetrieveUserQuery();
  const location = useLocation();

  if (loadingUser) {
    return <span className="loading loading-ring loading-lg"></span>;
  } else if (user) {
    return children;
  } else {
    const url = location.pathname + location.search + location.hash;
    return <Navigate to="/login" state={{ next: url }} />;
  }
};

export default PrivateRoute;
