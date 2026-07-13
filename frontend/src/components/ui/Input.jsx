import { useId } from 'react';

export default function Input({
  label,
  error,
  helperText,
  className = '',
  id: externalId,
  ...props
}) {
  const generatedId = useId();
  const inputId = externalId || generatedId;
  const errorId = error ? `${inputId}-error` : undefined;
  const helperId = helperText && !error ? `${inputId}-helper` : undefined;
  const describedBy = errorId || helperId;

  return (
    <div className="space-y-1">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-neutral-700"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy}
        className={`block w-full rounded-md border bg-white px-3 py-2 text-sm text-neutral-900 placeholder-neutral-400 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-0 disabled:opacity-50 disabled:bg-neutral-50 ${
          error
            ? 'border-error focus:ring-error'
            : 'border-neutral-300 hover:border-neutral-400'
        } ${className}`}
        {...props}
      />
      {error && (
        <p id={errorId} className="text-sm text-error" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={helperId} className="text-sm text-neutral-500">
          {helperText}
        </p>
      )}
    </div>
  );
}
