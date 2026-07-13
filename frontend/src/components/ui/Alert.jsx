const variants = {
  error: 'bg-error-bg border-error/30 text-error',
  success: 'bg-success-bg border-success/30 text-success',
  warning: 'bg-warning-bg border-warning/30 text-warning',
  info: 'bg-info-bg border-info/30 text-info',
};

export default function Alert({
  variant = 'error',
  dismissible = false,
  onDismiss,
  className = '',
  children,
}) {
  return (
    <div
      role="alert"
      className={`rounded-md border px-4 py-3 text-sm ${variants[variant]} ${className}`}
    >
      <div className="flex items-start justify-between gap-2">
        <span>{children}</span>
        {dismissible && (
          <button
            onClick={onDismiss}
            className="shrink-0 opacity-60 hover:opacity-100 transition-opacity cursor-pointer bg-transparent border-none p-0 leading-none"
            aria-label="Dismiss"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M10.5 3.5l-7 7m0-7l7 7"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
