import { useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "sonner";
import {
  useLoginMutation,
  useLogoutMutation,
  useRetrieveUserQuery,
} from "../redux/features/auth/authApiSlice";
import { useLocation, useNavigate } from "react-router-dom";

export default function useAuth() {
  const [formErrors, setFormErrors] = useState({});
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const dispatch = useDispatch();

  const [login] = useLoginMutation();
  const [logout] = useLogoutMutation();
  const { isAuthenticated } = useSelector((state) => state.auth);
  const {
    data: user,
    isLoading: loadingUser,
    refetch,
  } = useRetrieveUserQuery(undefined, {
    skip: !isAuthenticated,
  });
  const adminUser = user?.is_staff;

  const navigate = useNavigate();
  const location = useLocation();
  const [nextPage] = useState(location.state?.next);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleValidation = () => {
    const errors = {};
    if (!formData.email.trim()) errors.email = "Email must not be empty.";
    if (!formData.password.trim())
      errors.password = "Password must not be empty.";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!handleValidation()) return;

    setIsSubmitting(true);
    try {
      await login({
        email: formData.email.trim(),
        password: formData.password.trim(),
      }).unwrap();
      // toast.success("Login successful!");
    } catch (err) {
      toast.error("Invalid email or password");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout().unwrap();
      toast.success("Logout successful!");
    } catch (err) {
      toast.error("Logout failed. Please try again.");
    }
  };
  return {
    formErrors,
    formData,
    user,
    nextPage,
    adminUser,
    isSubmitting,
    loadingUser,
    setFormData,
    handleLogin,
    handleLogout,
  };
}
