export default function Toggle({ label, enabled, onChange, className = '' }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {label && (
        <span className="text-sm text-neutral-600">{label}</span>
      )}
      <div
        role="switch"
        aria-checked={enabled}
        tabIndex={0}
        onClick={() => onChange(!enabled)}
        onKeyDown={(e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            onChange(!enabled);
          }
        }}
        className={`relative inline-flex h-6 w-11 cursor-pointer items-center rounded-full border transition-colors focus-visible:outline-2 focus-visible:outline-primary-600 focus-visible:outline-offset-2 ${
          enabled
            ? 'border-primary-600 bg-primary-600'
            : 'border-neutral-300 bg-white'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-[5.5px]' : 'translate-x-[3px]'
          }`}
        />
      </div>
    </div>
  );
}
