import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import Spinner from './ui/Spinner';

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <main className="flex items-center justify-center min-h-[calc(100vh-3.5rem)]">
        <Spinner size="lg" />
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
