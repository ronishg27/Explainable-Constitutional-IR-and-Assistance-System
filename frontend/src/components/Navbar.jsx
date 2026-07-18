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
    <nav className="sticky top-0 z-40 border-b border-neutral-200 bg-white/80 backdrop-blur-lg" aria-label="Main navigation">
      <div className="mx-auto flex h-14 max-w-[1300px] items-center justify-between px-6">
        <Link
          to="/"
          className="flex items-center gap-2.5 text-sm font-semibold text-neutral-900 no-underline"
        >
          <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-primary-600 text-white text-xs font-bold">C</span>
          Constitutional Assistant
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex md:items-center md:gap-1">
          {navLinks.map(({ label, to }) => {
            const active = isActive(to);
            return (
              <Link
                key={to}
                to={to}
                aria-current={active ? 'page' : undefined}
                className={`relative px-3.5 py-2 text-sm no-underline transition-all duration-200 rounded-xl ${
                  active
                    ? 'font-medium text-primary-600 bg-primary-50'
                    : 'text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100'
                }`}
              >
                {label}
              </Link>
            );
          })}

          {user ? (
            <div className="flex items-center gap-3 ml-4 pl-4 border-l border-neutral-200">
              <Link
                to="/history"
                className={`px-3.5 py-2 text-sm no-underline transition-all duration-200 rounded-xl ${
                  isActive('/history')
                    ? 'font-medium text-primary-600 bg-primary-50'
                    : 'text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100'
                }`}
              >
                History
              </Link>
              <span className="text-sm text-neutral-400">{user.fullname}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-neutral-500 hover:text-neutral-700 transition-all duration-200 bg-transparent border-none cursor-pointer px-2 py-1 rounded-lg hover:bg-neutral-100"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="ml-4 rounded-xl bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 no-underline transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.97]"
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
          className="flex md:hidden items-center justify-center h-9 w-9 rounded-xl text-neutral-500 hover:bg-neutral-100 transition-all duration-200 cursor-pointer bg-transparent border-none"
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
            {navLinks.map(({ label, to }) => {
              const active = isActive(to);
              return (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMenuOpen(false)}
                  aria-current={active ? 'page' : undefined}
                  className={`block rounded-xl px-3.5 py-2.5 text-sm no-underline transition-all duration-200 ${
                    active
                      ? 'bg-primary-50 font-medium text-primary-600'
                      : 'text-neutral-600 hover:bg-neutral-50'
                  }`}
                >
                  {label}
                </Link>
              );
            })}
            <hr className="border-neutral-200 my-2" />
            {user ? (
              <>
                <Link
                  to="/history"
                  onClick={() => setMenuOpen(false)}
                  className={`block rounded-xl px-3.5 py-2.5 text-sm no-underline transition-all duration-200 ${
                    isActive('/history')
                      ? 'bg-primary-50 font-medium text-primary-600'
                      : 'text-neutral-600 hover:bg-neutral-50'
                  }`}
                >
                  History
                </Link>
                <span className="block px-3.5 py-2.5 text-sm text-neutral-400">
                  {user.fullname}
                </span>
                <button
                  onClick={() => {
                    handleLogout();
                    setMenuOpen(false);
                  }}
                  className="block w-full rounded-xl px-3.5 py-2.5 text-left text-sm text-neutral-600 hover:bg-neutral-50 transition-all duration-200 bg-transparent border-none cursor-pointer"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login"
                onClick={() => setMenuOpen(false)}
                className="block rounded-xl bg-primary-600 px-3.5 py-2.5 text-sm font-medium text-white text-center no-underline hover:bg-primary-700 transition-all duration-200"
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
