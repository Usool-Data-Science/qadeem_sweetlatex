export default function InputField({
    name,
    label,
    type = 'text',
    placeholder,
    error,
    fieldRef,
}) {
    return (
        <div className="form-control w-full max-w-xs">
            {label && (
                <label htmlFor={name} className="label">
                    <span className="label-text">{label}</span>
                </label>
            )}
            <input
                id={name}
                name={name}
                type={type}
                placeholder={placeholder}
                ref={fieldRef}
                className="input input-bordered w-full"
            />
            {error && (
                <span className="text-error text-sm mt-1">{error}</span>
            )}
        </div>
    );
}
