import './Select.css'

/**
 * Custom Select Component with modern styling
 * @param {Object} props
 * @param {string} props.label - Label text for the select
 * @param {string} props.value - Currently selected value
 * @param {Function} props.onChange - Change handler
 * @param {Array} props.options - Array of option strings
 * @param {string} props.placeholder - Placeholder text
 * @param {boolean} props.disabled - Disabled state
 * @param {boolean} props.loading - Loading state
 * @param {string} props.error - Error message
 */
function Select({
    label,
    value,
    onChange,
    options = [],
    placeholder = 'Select an option',
    disabled = false,
    loading = false,
    error = null,
    id
}) {
    const handleChange = (e) => {
        onChange(e.target.value);
    };

    return (
        <div className={`select-wrapper ${disabled ? 'disabled' : ''} ${error ? 'has-error' : ''}`}>
            {label && (
                <label htmlFor={id} className="select-label">
                    {label}
                </label>
            )}
            <div className="select-container">
                <select
                    id={id}
                    value={value}
                    onChange={handleChange}
                    disabled={disabled || loading}
                    className="select-input"
                >
                    <option value="" disabled>
                        {loading ? 'Loading...' : placeholder}
                    </option>
                    {options.map((option) => (
                        <option key={option} value={option}>
                            {option.charAt(0).toUpperCase() + option.slice(1)}
                        </option>
                    ))}
                </select>
                <div className="select-arrow">
                    {loading ? (
                        <span className="loading-spinner" />
                    ) : (
                        <svg
                            width="12"
                            height="12"
                            viewBox="0 0 12 12"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                d="M2.5 4.5L6 8L9.5 4.5"
                                stroke="currentColor"
                                strokeWidth="1.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                    )}
                </div>
            </div>
            {error && <span className="select-error">{error}</span>}
        </div>
    );
}

export default Select;
