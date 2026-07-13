import { useState } from 'react';

export default function Accordion({
  items,
  className = '',
}) {
  const [openId, setOpenId] = useState(null);

  const toggle = (id) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <div className={`space-y-1 ${className}`}>
      {items.map((item) => {
        const isOpen = openId === item.id;
        return (
          <div key={item.id} className="border border-neutral-200 rounded-md overflow-hidden">
            <button
              onClick={() => toggle(item.id)}
              aria-expanded={isOpen}
              className="w-full flex items-center justify-between gap-3 px-3.5 py-2.5 text-left bg-white hover:bg-neutral-50 transition-colors cursor-pointer"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-neutral-900 truncate">
                  {item.title}
                </p>
                {item.subtitle && (
                  <p className="text-xs text-neutral-500 mt-0.5">
                    {item.subtitle}
                  </p>
                )}
              </div>
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                className={`shrink-0 text-neutral-400 transition-transform ${
                  isOpen ? 'rotate-180' : ''
                }`}
              >
                <path
                  d="M3.5 5.25L7 8.75L10.5 5.25"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
            {isOpen && (
              <div className="border-t border-neutral-200 bg-neutral-50 px-3.5 py-3 text-sm text-neutral-700 leading-relaxed">
                {item.content}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
