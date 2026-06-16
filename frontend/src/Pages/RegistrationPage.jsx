import { useNavigate } from "react-router-dom";
import GeneralInput from "../Components/InputTypes";
import { useRef, useState } from "react";
import Body from "../Components/Body";
import { useRegisterMutation } from "../redux/features/auth/authApiSlice";
import { toast } from "sonner";
import { getErrorMessage } from "../utils";

const NewUser = () => {
  const navigate = useNavigate();
  const [register] = useRegisterMutation();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    re_password: "",
  });

  const handleValidation = () => {
    const errors = {};

    if (!formData.first_name.trim())
      errors.first_name = "First name must not be empty";
    if (!formData.last_name.trim())
      errors.last_name = "Last name must not be empty";
    if (!formData.email.trim()) errors.email = "Email must not be empty";
    if (!formData.password.trim())
      errors.password = "Password must not be empty";
    if (formData.password.trim() !== formData.re_password.trim())
      errors.re_password = "Passwords must match";

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!handleValidation()) return;

    setIsSubmitting(true);
    try {
      await register({
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.trim(),
        password: formData.password.trim(),
        re_password: formData.re_password.trim(),
      }).unwrap();

      toast.success("Account created! Please log in.");
      navigate("/login");
    } catch (err) {
      const data = err?.data;
      if (data) {
        const mapped = {};
        if (data.email) mapped.email = data.email[0];
        if (data.password) mapped.password = data.password[0];
        if (data.non_field_errors) toast.error(data.non_field_errors[0]);
        if (Object.keys(mapped).length) {
          setFormErrors(mapped);
        } else {
          toast.error(getErrorMessage(err));
        }
      } else {
        toast.error(getErrorMessage(err));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Body>
      <h2 className="text-3xl text-center font-extrabold text-slate-100 mt-8 mb-4 font-courier">
        CREATE ACCOUNT
      </h2>
      <div className="flex justify-center items-center">
        <div className="w-full max-w-lg shadow-lg p-8">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col items-center gap-6"
          >
            <GeneralInput
              name="first_name"
              label="First Name"
              placeholder="FIRST NAME"
              error={formErrors.first_name}
              value={formData.first_name}
              onChange={(e) =>
                setFormData({ ...formData, first_name: e.target.value })
              }
            />
            <GeneralInput
              name="last_name"
              label="Last Name"
              placeholder="LAST NAME"
              error={formErrors.last_name}
              value={formData.last_name}
              onChange={(e) =>
                setFormData({ ...formData, last_name: e.target.value })
              }
            />
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
            <GeneralInput
              name="re_password"
              label="Confirm Password"
              type="password"
              placeholder="CONFIRM PASSWORD"
              error={formErrors.re_password}
              value={formData.re_password}
              onChange={(e) =>
                setFormData({ ...formData, re_password: e.target.value })
              }
            />

            <button
              type="submit"
              className="w-full p-2 mt-6 text-lg font-bold border border-gray-50 text-slate-100 bg-transparent hover:text-red-500 transition-all duration-300 ease-in-out mb-8 font-courier"
              aria-busy={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <progress className="progress w-6 h-6 text-slate-100"></progress>
                  Registering...
                </span>
              ) : (
                "CREATE MY PROFILE"
              )}
            </button>
          </form>

          <h2 className="text-2xl text-center font-extrabold text-slate-100 my-4 font-courier">
            <a href="/login">ALREADY HAVE AN ACCOUNT</a>
          </h2>
        </div>
      </div>
    </Body>
  );
};

export default NewUser;
