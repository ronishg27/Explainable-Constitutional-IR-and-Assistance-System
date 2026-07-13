export default function Card({
  header,
  footer,
  children,
  className = '',
  ...props
}) {
  return (
    <div
      className={`rounded-lg border border-neutral-200 bg-white ${className}`}
      {...props}
    >
      {header && (
        <div className="border-b border-neutral-200 px-4 py-3">
          {typeof header === 'string' ? (
            <h3 className="text-sm font-semibold text-neutral-900">{header}</h3>
          ) : (
            header
          )}
        </div>
      )}
      <div className="px-4 py-4">{children}</div>
      {footer && (
        <div className="border-t border-neutral-200 px-4 py-3">
          {footer}
        </div>
      )}
    </div>
  );
}
