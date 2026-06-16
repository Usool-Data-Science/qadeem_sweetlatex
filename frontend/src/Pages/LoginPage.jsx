import { useLocation, useNavigate } from "react-router-dom";
import GeneralInput from "../Components/InputTypes";
import { useEffect, useRef, useState } from "react";
import Body from "../Components/Body";
import {
  useLoginMutation,
  useRetrieveUserQuery,
} from "../redux/features/auth/authApiSlice";
import { setAuth } from "../redux/features/auth/authSlice";
import { toast } from "sonner";
import useAuth from "../hooks/use-auth";

const LoginPage = () => {
  const navigate = useNavigate();
  const {
    user,
    adminUser,
    nextPage,
    isSubmitting,
    formErrors,
    formData,
    setFormData,
    handleLogin,
  } = useAuth();

  // navigates once user is populated after retrieveUser refetches
  useEffect(() => {
    if (!user) return;
    navigate(nextPage || (adminUser ? "/admin" : "/home"));
  }, [user, adminUser, navigate, nextPage]);

  return (
    <Body>
      <h2 className="text-3xl text-center font-extrabold text-slate-100 mt-8 mb-4 font-courier">
        LOGIN
      </h2>
      <div className="flex justify-center items-center bg-gren-800">
        <div className="w-full max-w-lg shadow-lg p-8 bg-ble-800">
          <form
            onSubmit={handleLogin}
            className="flex flex-col items-center gap-6 bg-rd-800"
          >
            <GeneralInput
              name="email"
              label="Email"
              placeholder="EMAIL"
              error={formErrors.email}
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
            />
            <GeneralInput
              name="password"
              label="Password"
              type="password"
              placeholder="PASSWORD"
              error={formErrors.password}
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
            />
            <button
              type="submit"
              className="w-full p-2 mt-6 text-lg font-bold border border-gray-50 text-slate-100 bg-transparent hover:text-red-500 transition-all duration-300 ease-in-out mb-8"
              aria-busy={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center font-courier justify-center gap-2">
                  <progress className="progress w-6 h-6 text-slate-100"></progress>
                  Processing...
                </span>
              ) : (
                "NEXT"
              )}
            </button>
          </form>
          <small className="font-courier text-center text-sm text-slate-400">
            Forgot Password?{" "}
            <a href="/reset-request" className="text-blue-300">
              Reset it here
            </a>
          </small>
          <h2 className="text-2xl text-center font-extrabold text-slate-100 my-4 font-courier">
            <a href="/register">CREATE AN ACCOUNT</a>
          </h2>
        </div>
      </div>
    </Body>
  );
};

export default LoginPage;
