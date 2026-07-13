import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';

const navLinks = [
  { label: 'Home', to: '/' },
  { label: 'About', to: '/about' },
  { label: 'How It Works', to: '/how-it-works' },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const isActive = (to) => location.pathname === to;

  return (
    <nav className="sticky top-0 z-40 border-b border-neutral-200 bg-white" aria-label="Main navigation">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link
          to="/"
          className="flex items-center gap-2 text-base font-semibold text-neutral-900 no-underline"
        >
          Constitutional Assistant
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex md:items-center md:gap-6">
          {navLinks.map(({ label, to }) => (
            <Link
              key={to}
              to={to}
              aria-current={isActive(to) ? 'page' : undefined}
              className={`text-sm no-underline transition-colors ${
                isActive(to)
                  ? 'font-medium text-neutral-900'
                  : 'text-neutral-500 hover:text-neutral-800'
              }`}
            >
              {label}
            </Link>
          ))}

          {user ? (
            <div className="flex items-center gap-4 border-l border-neutral-200 pl-4">
              <Link
                to="/history"
                className={`text-sm no-underline transition-colors ${
                  isActive('/history')
                    ? 'font-medium text-neutral-900'
                    : 'text-neutral-500 hover:text-neutral-800'
                }`}
              >
                History
              </Link>
              <span className="text-sm text-neutral-400">{user.fullname}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-neutral-500 hover:text-neutral-800 transition-colors bg-transparent border-none cursor-pointer"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700 no-underline transition-colors"
            >
              Sign In
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          className="flex md:hidden items-center justify-center h-8 w-8 rounded-md text-neutral-600 hover:bg-neutral-100 transition-colors cursor-pointer bg-transparent border-none"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            {menuOpen ? (
              <path
                d="M5 5l10 10M15 5L5 15"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            ) : (
              <path
                d="M3 5h14M3 10h14M3 15h14"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="border-t border-neutral-200 bg-white md:hidden">
          <div className="space-y-1 px-4 py-3">
            {navLinks.map(({ label, to }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMenuOpen(false)}
                aria-current={isActive(to) ? 'page' : undefined}
                className={`block rounded-md px-3 py-2 text-sm no-underline transition-colors ${
                  isActive(to)
                    ? 'bg-neutral-100 font-medium text-neutral-900'
                    : 'text-neutral-600 hover:bg-neutral-50'
                }`}
              >
                {label}
              </Link>
            ))}
            <hr className="border-neutral-200 my-2" />
            {user ? (
              <>
                <Link
                  to="/history"
                  onClick={() => setMenuOpen(false)}
                  className={`block rounded-md px-3 py-2 text-sm no-underline transition-colors ${
                    isActive('/history')
                      ? 'bg-neutral-100 font-medium text-neutral-900'
                      : 'text-neutral-600 hover:bg-neutral-50'
                  }`}
                >
                  History
                </Link>
                <span className="block px-3 py-2 text-sm text-neutral-400">
                  {user.fullname}
                </span>
                <button
                  onClick={() => {
                    handleLogout();
                    setMenuOpen(false);
                  }}
                  className="block w-full rounded-md px-3 py-2 text-left text-sm text-neutral-600 hover:bg-neutral-50 transition-colors bg-transparent border-none cursor-pointer"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login"
                onClick={() => setMenuOpen(false)}
                className="block rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white text-center no-underline hover:bg-primary-700 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
