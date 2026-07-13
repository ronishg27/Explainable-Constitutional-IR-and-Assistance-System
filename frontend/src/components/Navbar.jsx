import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';

const navLinks = [
  { label: 'Home', to: '/' },
  { label: 'About', to: '/about' },
  { label: 'How it Works', to: '/how-it-works' },
];

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <nav className="sticky top-0" style={{ backgroundColor: 'rgb(225, 225, 234)', color: 'gray-900' }}>
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-1.5 no-underline">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-hero">
            <img src="src/assets/balance.png" alt="" />
          </div>
          <span
            className="flex text-black text-foreground text-2xl font-semibold p-1"
            style={{ fontFamily: 'var(--font-heading)' }}
          >
            Constitutional Assistant
          </span>
        </Link>

        <div className="flex items-center gap-5">
          <ul className="text-gray-500 flex items-center gap-5.5 list-none m-0 p-0">
            {navLinks.map(({ label, to }) => (
              <li key={label}>
                <Link to={to} className="text-md font-bold hover:text-gray-900 no-underline">
                  {label}
                </Link>
              </li>
            ))}
          </ul>

          {user ? (
            <div className="flex items-center gap-3">
              <Link
                to="/history"
                className="text-sm text-gray-500 hover:text-gray-900 no-underline"
              >
                History
              </Link>
              <span className="text-sm text-gray-600">{user.fullname}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-900 bg-transparent border-none cursor-pointer"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="text-sm font-medium text-blue-600 hover:text-blue-800 no-underline"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
