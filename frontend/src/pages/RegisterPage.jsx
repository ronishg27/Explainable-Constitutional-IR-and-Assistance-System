import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Alert from '../components/ui/Alert';
import Card from '../components/ui/Card';

export default function RegisterPage() {
  const [fullname, setFullname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await register(fullname, email, password);
      navigate('/login', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] px-4">
      <Card className="w-full max-w-sm">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <h1 className="text-lg font-semibold text-neutral-900">Create Account</h1>
            <p className="text-sm text-neutral-500 mt-1">
              Start exploring the Constitution
            </p>
          </div>

          {error && (
            <Alert variant="error">{error}</Alert>
          )}

          <Input
            label="Full Name"
            type="text"
            required
            value={fullname}
            onChange={(e) => setFullname(e.target.value)}
            placeholder="Your full name"
          />

          <Input
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />

          <Input
            label="Password"
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            helperText="At least 6 characters"
          />

          <Button
            type="submit"
            loading={submitting}
            className="w-full"
          >
            Create Account
          </Button>

          <p className="text-center text-sm text-neutral-500">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 underline">
              Sign In
            </Link>
          </p>
        </form>
      </Card>
    </main>
  );
}
