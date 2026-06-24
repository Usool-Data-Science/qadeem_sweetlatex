import { useNavigate } from "react-router-dom";
import Body from "../Components/Body";
import { useRef, useState } from "react";
import GeneralInput from "../Components/InputTypes";
import { toast } from "sonner";
import {
  useChangeUserPasswordMutation,
  useUpdateUserProfileMutation,
} from "../redux/features/auth/authApiSlice";
import useAuth from "../hooks/use-auth";

const ADDRESS_TYPES = ["home", "postal", "work"];

const EditUser = () => {
  const { user } = useAuth();
  const [updateUser] = useUpdateUserProfileMutation();
  const [changeUserPassword] = useChangeUserPasswordMutation();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [activeTab, setActiveTab] = useState("personal"); // "personal" | "address" | "security"

  // address form state
  const [addressType, setAddressType] = useState("home");
  const [isDefault, setIsDefault] = useState(false);

  const firstNameField = useRef();
  const lastNameField = useRef();
  const emailField = useRef();
  const contactField = useRef();
  const newPasswordField = useRef();
  const reNewPasswordField = useRef();
  const currentPasswordField = useRef();

  // address refs
  const streetField = useRef();
  const cityField = useRef();
  const stateField = useRef();
  const countryField = useRef();

  const handleUpdates = async (profilePayload, securityPayload) => {
    setIsLoading(true);

    try {
      if (Object.keys(profilePayload).length > 0) {
        await updateUser(profilePayload).unwrap();
      }

      if (Object.keys(securityPayload).length > 0) {
        await changeUserPassword(securityPayload).unwrap();
      }

      toast.success("Changes saved successfully!");
      navigate("/myaccount");
    } catch (err) {
      toast.error(
        err?.data?.detail ||
          err?.data?.message ||
          "Something went wrong. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidation = () => {
    const errors = {};
    if (activeTab === "personal") {
      if (!firstNameField.current.value.trim())
        errors.first_name = "First name must not be empty";
      if (!lastNameField.current.value.trim())
        errors.last_name = "Last name must not be empty";
      if (!emailField.current.value.trim())
        errors.email = "Email must not be empty";
    }
    if (activeTab === "address") {
      if (!streetField.current.value.trim())
        errors.street = "Street must not be empty";
      if (!cityField.current.value.trim())
        errors.city = "City must not be empty";
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!handleValidation()) return;

    let profilePayload = {};
    let securityPayload = {};

    if (activeTab === "personal") {
      Object.assign(profilePayload, {
        first_name: firstNameField.current.value.trim(),
        last_name: lastNameField.current.value.trim(),
        email: emailField.current.value.trim(),
        phone_number: contactField.current.value.trim(),
      });
    }

    if (activeTab === "address") {
      Object.assign(profilePayload, {
        street: streetField.current.value.trim(),
        city: cityField.current.value.trim(),
        state: stateField.current.value.trim(),
        country: countryField.current.value.trim(),
        address_type: addressType,
        is_default: isDefault,
      });
    }

    if (activeTab === "security") {
      securityPayload = {
        new_password: newPasswordField.current.value,
        re_new_password: reNewPasswordField.current.value,
        current_password: currentPasswordField.current.value,
      };
    }

    await handleUpdates(profilePayload, securityPayload);
  };

  // find address by type from user.addresses array
  const getAddress = (type) =>
    user?.addresses?.find((a) => a.address_type === type) || null;

  const defaultAddress = user?.addresses?.find((a) => a.is_default) || null;

  if (!user) return null;

  const tabs = [
    { id: "personal", label: "Personal Info" },
    { id: "address", label: "Addresses" },
    { id: "security", label: "Security" },
  ];

  return (
    <Body>
      <div className="min-h-screen font-courier bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-4 py-10">
        <div className="mx-auto max-w-3xl">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
              Edit Profile
            </h1>
            <p className="mt-3 text-sm md:text-base text-slate-400">
              Update your personal information and account credentials.
            </p>
          </div>

          {/* Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30">
            {/* Tabs */}
            <div className="flex border-b border-slate-800">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    setActiveTab(tab.id);
                    setFormErrors({});
                  }}
                  className={`flex-1 px-4 py-4 text-sm font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? "text-white border-b-2 border-white -mb-[2px]"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="px-6 py-6 md:px-8 md:py-8">
              {/* ── Personal Info Tab ── */}
              {activeTab === "personal" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-100">
                  <GeneralInput
                    showLabel
                    name="first_name"
                    label="First Name"
                    value={user.first_name}
                    error={formErrors.first_name}
                    fieldRef={firstNameField}
                  />
                  <GeneralInput
                    showLabel
                    name="last_name"
                    label="Last Name"
                    value={user.last_name}
                    error={formErrors.last_name}
                    fieldRef={lastNameField}
                  />
                  <div className="md:col-span-2">
                    <GeneralInput
                      showLabel
                      name="email"
                      label="Email Address"
                      value={user.email}
                      error={formErrors.email}
                      fieldRef={emailField}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <GeneralInput
                      showLabel
                      name="phone_number"
                      label="Phone Number"
                      type="tel"
                      value={user.phone_number}
                      error={formErrors.phone_number}
                      fieldRef={contactField}
                    />
                  </div>
                </div>
              )}

              {/* ── Address Tab ── */}
              {activeTab === "address" && (
                <div className="space-y-6">
                  {/* Existing addresses overview */}
                  {user.addresses?.length > 0 && (
                    <div className="space-y-3 mb-6">
                      <p className="text-xs uppercase tracking-widest text-slate-500">
                        Saved Addresses
                      </p>
                      {user.addresses.map((addr) => (
                        <div
                          key={addr.id}
                          className="flex items-start justify-between rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400 border border-slate-700 rounded px-1.5 py-0.5">
                                {addr.address_type}
                              </span>
                              {addr.is_default && (
                                <span className="text-xs font-medium text-white bg-slate-700 rounded px-1.5 py-0.5">
                                  Default
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-white mt-1">
                              {addr.street}, {addr.city}
                            </p>
                            <p className="text-xs text-slate-500">
                              {addr.state}, {addr.country}
                            </p>
                          </div>
                          {/* clicking Edit pre-selects that address type */}
                          <button
                            type="button"
                            onClick={() => {
                              setAddressType(addr.address_type);
                              setIsDefault(addr.is_default);
                            }}
                            className="text-xs text-slate-400 hover:text-white transition ml-4 mt-1 shrink-0"
                          >
                            Edit
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Address type selector */}
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">
                      {getAddress(addressType)
                        ? `Edit ${addressType} address`
                        : `Add ${addressType} address`}
                    </p>
                    <div className="flex gap-2 mb-6">
                      {ADDRESS_TYPES.map((type) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setAddressType(type)}
                          className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-all duration-200 capitalize ${
                            addressType === type
                              ? "border-white bg-white text-slate-900"
                              : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-300"
                          }`}
                        >
                          {type}
                          {getAddress(type) && (
                            <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-slate-400 align-middle" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Address fields */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-100">
                    <div className="md:col-span-2">
                      <GeneralInput
                        showLabel
                        name="street"
                        label="Street Address"
                        value={getAddress(addressType)?.street || ""}
                        error={formErrors.street}
                        fieldRef={streetField}
                        key={`street-${addressType}`}
                      />
                    </div>
                    <GeneralInput
                      showLabel
                      name="city"
                      label="City"
                      value={getAddress(addressType)?.city || ""}
                      error={formErrors.city}
                      fieldRef={cityField}
                      key={`city-${addressType}`}
                    />
                    <GeneralInput
                      showLabel
                      name="state"
                      label="State"
                      value={getAddress(addressType)?.state || ""}
                      error={formErrors.state}
                      fieldRef={stateField}
                      key={`state-${addressType}`}
                    />
                    <GeneralInput
                      showLabel
                      name="country"
                      label="Country"
                      defaultValue={
                        getAddress(addressType)?.country || "Nigeria"
                      }
                      fieldRef={countryField}
                      key={`country-${addressType}`}
                    />

                    {/* Set as default toggle */}
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setIsDefault((v) => !v)}
                        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ${
                          isDefault ? "bg-white" : "bg-slate-700"
                        }`}
                      >
                        <span
                          className={`pointer-events-none inline-block h-4 w-4 rounded-full shadow transform transition duration-200 ${
                            isDefault
                              ? "translate-x-4 bg-slate-900"
                              : "translate-x-0 bg-slate-400"
                          }`}
                        />
                      </button>
                      <span className="text-sm text-slate-400">
                        Set as default address
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Security Tab ── */}
              {activeTab === "security" && (
                <div className="space-y-6">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3 text-sm text-slate-400">
                    Leave password fields empty if you don't want to change your
                    password. Your current password is required to set a new
                    one.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-100">
                    <GeneralInput
                      showLabel
                      name="new_password"
                      label="New Password"
                      type="password"
                      placeholder="Enter new password"
                      fieldRef={newPasswordField}
                    />
                    <GeneralInput
                      showLabel
                      name="re_new_password"
                      label="Confirm Password"
                      type="password"
                      placeholder="Confirm new password"
                      fieldRef={reNewPasswordField}
                    />
                    <GeneralInput
                      showLabel
                      name="current_password"
                      label="Current Password"
                      type="password"
                      placeholder="Required to change password"
                      fieldRef={currentPasswordField}
                    />
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-4 pt-8 mt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => navigate("/myaccount")}
                  className="w-full sm:w-auto rounded-xl border border-slate-700 px-6 py-3 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-slate-500 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full sm:w-auto rounded-xl bg-white px-6 py-3 text-sm font-semibold text-slate-900 shadow-lg shadow-white/10 transition-all duration-200 hover:scale-[1.02] hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isLoading ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Body>
  );
};

export default EditUser;
