import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import Body from "../Components/Body";
import GeneralInput from "../Components/InputTypes";
import { useResetPasswordConfirmMutation } from "../redux/features/auth/authApiSlice";

export default function ResetPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [resetPasswordConfirm] = useResetPasswordConfirmMutation();
  const [formData, setFormData] = useState({
    password: "",
    password2: "",
  });
  const navigate = useNavigate();
  const { uid, token } = useParams();

  useEffect(() => {
    if (!token || !uid) {
      navigate("/");
    } else {
      document.getElementById("password")?.focus();
    }
  }, [token, uid, navigate]);

  const onSubmit = async (event) => {
    event.preventDefault();

    setIsSubmitting(true);

    if (formData.password !== formData.password2) {
      setFormErrors({
        password2: "New passwords don't match",
      });

      setIsSubmitting(false);
      return;
    }

    try {
      await resetPasswordConfirm({
        uid,
        token,
        new_password: formData.password,
        re_new_password: formData.password2,
      }).unwrap();

      setFormErrors({});

      toast.success("Your password has been reset.");

      navigate("/login");
    } catch (error) {
      console.log(error);

      if (error?.data) {
        setFormErrors(error.data);
      } else {
        toast.error("Password could not be reset. Please try again.");

        navigate("/reset-request");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Body loginButton>
      <h2 className="text-3xl text-center font-extrabold text-slate-100 mt-8 mb-4 font-courier">
        Reset Your Password
      </h2>

      <div className="flex justify-center items-center">
        <div className="w-full max-w-lg bg-transparent shadow-lg p-8">
          <form
            onSubmit={onSubmit}
            className="flex flex-col items-center gap-6"
          >
            <GeneralInput
              name="password"
              label="New Password"
              type="password"
              placeholder="Enter your new password"
              error={formErrors.password}
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
            />

            <GeneralInput
              name="password2"
              label="Confirm Password"
              type="password"
              placeholder="Re-enter your new password"
              error={formErrors.password2}
              value={formData.password2}
              onChange={(e) =>
                setFormData({ ...formData, password2: e.target.value })
              }
            />

            <button
              type="submit"
              className="w-full md:w-4/5 lg:w-2/3 mt-6 text-lg font-bold text-slate-100 transition-all duration-300 ease-in-out mb-8 border border-gray-50 hover:text-red-500 p-3 font-courier"
              aria-busy={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <progress className="progress w-6 h-6 text-slate-100"></progress>
                  Processing...
                </span>
              ) : (
                "Reset"
              )}
            </button>
          </form>
        </div>
      </div>
    </Body>
  );
}
