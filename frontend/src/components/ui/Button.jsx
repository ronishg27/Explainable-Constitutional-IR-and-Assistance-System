const variants = {
  primary:
    'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-700 disabled:opacity-50 disabled:hover:bg-primary-600 shadow-sm hover:shadow-md',
  secondary:
    'bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 active:bg-neutral-100 disabled:opacity-50 disabled:hover:bg-white hover:shadow-sm',
  danger:
    'text-error hover:bg-error-bg active:bg-error-bg disabled:opacity-50',
  ghost:
    'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 active:bg-neutral-200 disabled:opacity-50',
};

const sizes = {
  sm: 'text-xs px-3 py-1.5',
  md: 'text-sm px-5 py-2.5',
  lg: 'text-base px-5 py-2.5',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  children,
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-xl font-medium transition-all duration-200 cursor-pointer disabled:cursor-not-allowed active:scale-[0.97] ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {loading ? (
        <>
          <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <span>{children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
