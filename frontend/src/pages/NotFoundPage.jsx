import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)] px-4">
      <h1 className="text-2xl font-semibold text-neutral-900">404</h1>
      <p className="mt-2 text-sm text-neutral-500">Page not found</p>
      <Link
        to="/"
        className="mt-4 rounded-md bg-primary-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-primary-700 no-underline transition-colors"
      >
        Go Home
      </Link>
    </main>
  );
}
