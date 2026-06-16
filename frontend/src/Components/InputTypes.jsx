import { useState } from "react";
import Select from "react-select";

/* -------------------------
   GENERAL INPUT COMPONENT
------------------------- */

const GeneralInput = ({
  showLabel,
  name,
  label,
  type = "text",
  placeholder,
  error,
  onChange,
  value,
}) => {
  // const [inputValue, setInputValue] = useState(value || "");

  // const handleChange = (e) => {
  //   if (type === "file") {
  //     const files = e.target.files;
  //     setInputValue(files?.length > 1 ? files : files[0]);
  //   } else {
  //     setInputValue(e.target.value);
  //   }
  // };

  const baseClasses =
    "w-full p-2 bg-transparent text-slate-200 font-courier focus:outline-none focus:ring-0";

  const inputStyles =
    type === "textarea"
      ? `${baseClasses} border-2 border-white focus:border-white`
      : `${baseClasses} border-b-2 border-white focus:border-white`;

  return (
    <div className="w-full mb-4">
      {showLabel && label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-white mb-1"
        >
          {label}
        </label>
      )}

      {type === "textarea" ? (
        <textarea
          id={name}
          name={name}
          rows={5}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={inputStyles}
        />
      ) : type === "file" ? (
        <input
          id={name}
          type="file"
          name={name}
          multiple
          value={value}
          onChange={onChange}
          className="file-input file-input-bordered border-white w-full bg-transparent text-white"
        />
      ) : (
        <input
          id={name}
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete="off"
          className={inputStyles}
        />
      )}

      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
};

export default GeneralInput;

/* -------------------------
   SELECT INPUT COMPONENT
------------------------- */

export const SelectInput = ({
  label,
  name,
  options,
  formData,
  setFormData,
  multiple,
}) => {
  const handleChange = (selected) => {
    const values = Array.isArray(selected)
      ? selected.map((opt) => opt.value)
      : selected?.value || "";

    setFormData({ ...formData, [name]: values });
  };

  return (
    <div className="w-full mb-4">
      <label className="block text-sm font-medium text-white mb-2">
        {label}
      </label>

      <Select
        name={name}
        options={options}
        isMulti={multiple}
        value={
          multiple
            ? options.filter((o) => formData[name]?.includes(o.value))
            : options.find((o) => o.value === formData[name])
        }
        onChange={handleChange}
        styles={{
          control: (base) => ({
            ...base,
            backgroundColor: "transparent",
            borderColor: "#ffffff",
            boxShadow: "none",
            padding: "2px 6px",
            ":hover": {
              borderColor: "#ffffff",
            },
          }),

          menu: (base) => ({
            ...base,
            backgroundColor: "#000",
            border: "1px solid #fff",
          }),

          option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused ? "#222" : "#000",
            color: "#fff",
            cursor: "pointer",
          }),

          singleValue: (base) => ({
            ...base,
            color: "#fff",
          }),

          multiValue: (base) => ({
            ...base,
            backgroundColor: "#fff",
          }),

          multiValueLabel: (base) => ({
            ...base,
            color: "#000",
          }),

          multiValueRemove: (base) => ({
            ...base,
            color: "#000",
            ":hover": {
              backgroundColor: "#ff4444",
              color: "#fff",
            },
          }),

          placeholder: (base) => ({
            ...base,
            color: "#ccc",
          }),

          input: (base) => ({
            ...base,
            color: "#fff",
          }),
        }}
      />
    </div>
  );
};
