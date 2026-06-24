import { useEffect, useRef, useState } from "react";
import Body from "../Components/Body";
import GeneralInput from "./InputTypes";
import { useContactSupportMutation } from "../redux/features/auth/authApiSlice";
import { toast } from "sonner";

const ContactPage = () => {
  const [formData, setFormData] = useState({
    email: "",
    subject: "",
    message: "",
  });
  const [formErrors, setFormErrors] = useState({});

  const [contactSupport, { isLoading, isSuccess, error }] =
    useContactSupportMutation();

  const handleValidation = () => {
    const errors = {};

    if (!formData.email.trim()) errors.email = "Email cannot be empty!";
    if (!formData.subject.trim()) errors.subject = "Subject cannot be empty!";
    if (!formData.message.trim()) errors.message = "Message cannot be empty!";

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const clearForm = () => {
    setFormData({
      email: "",
      subject: "",
      message: "",
    });
    setFormErrors({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!handleValidation()) return;

    try {
      const response = await contactSupport({
        email: formData.email.trim(),
        subject: formData.subject.trim(),
        body: formData.message.trim(),
      }).unwrap();
      clearForm();
      toast.success("Message received!");
    } catch (error) {
      setFormErrors(
        error?.data || {
          general: "Something went wrong. Please try again.",
        },
      );
      toast.error(error?.data?.general || "Failed to send message.");
    }
  };

  return (
    <Body loginButton>
      <h2 className="text-3xl text-center font-extrabold text-slate-100 mt-8 mb-4 font-courier">
        CONTACT
      </h2>

      <div className="flex justify-center items-center">
        <div className="w-full max-w-lg bg-transparent shadow-lg p-8">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col items-center gap-6 font-courier"
          >
            <GeneralInput
              name="email"
              label="Email"
              placeholder="Enter your email"
              error={formErrors.email}
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
            />

            <GeneralInput
              name="subject"
              label="Subject"
              placeholder="Enter subject"
              error={formErrors.subject}
              value={formData.subject}
              onChange={(e) =>
                setFormData({ ...formData, subject: e.target.value })
              }
            />

            <GeneralInput
              name="message"
              type="textarea"
              label="Message"
              placeholder="Write your message..."
              error={formErrors.message}
              value={formData.message}
              onChange={(e) =>
                setFormData({ ...formData, message: e.target.value })
              }
            />

            <button
              type="submit"
              className="w-full md:w-4/5 lg:w-2/3 mt-6 text-lg font-bold text-slate-100 transition-all duration-300 ease-in-out mb-8 border border-gray-50 hover:text-red-500 p-3 font-courier"
              aria-busy={isLoading}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <progress className="progress w-6 h-6 text-slate-100" />
                  Sending...
                </span>
              ) : (
                "Send"
              )}
            </button>
          </form>
        </div>
      </div>
    </Body>
  );
};

export default ContactPage;
