import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="text-center mt-24">
      <h1 className="text-4xl font-bold text-gray-900">404</h1>
      <p className="text-gray-500 mt-2">Page not found</p>
      <Link to="/" className="text-blue-600 text-sm mt-4 inline-block no-underline">
        Go Home
      </Link>
    </div>
  );
}
