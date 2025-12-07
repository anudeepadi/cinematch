import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Film } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import toast from 'react-hot-toast';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await login({ email, password });
      toast.success('Welcome back!');
      navigate('/recommendations');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 mb-12">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/30">
              <Film className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">
              <span className="text-white">Cine</span>
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">Match</span>
            </span>
          </Link>

          <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
          <p className="text-zinc-400 mb-8">Sign in to continue your movie journey</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              icon={<Mail size={20} />}
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              icon={<Lock size={20} />}
              required
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-zinc-700 bg-zinc-900 text-amber-500 focus:ring-amber-500/30"
                />
                <span className="text-sm text-zinc-400">Remember me</span>
              </label>
              <Link to="/forgot-password" className="text-sm text-amber-400 hover:text-amber-300 transition-colors">
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={isLoading}
              icon={<ArrowRight size={20} />}
              iconPosition="right"
            >
              Sign in
            </Button>
          </form>

          <p className="text-center text-zinc-500 mt-8">
            Don't have an account?{' '}
            <Link to="/register" className="text-amber-400 hover:text-amber-300 font-medium transition-colors">
              Create one
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right side - Visual */}
      <div className="hidden lg:block lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-amber-600/20 via-orange-600/20 to-red-600/20" />
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1200)',
            filter: 'brightness(0.4)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent" />

        <div className="relative z-10 h-full flex flex-col justify-end p-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <blockquote className="text-2xl font-light text-white/90 mb-4 leading-relaxed">
              "The perfect movie for every mood, every moment, every person you're with."
            </blockquote>
            <p className="text-amber-400 font-medium">Discover your next favorite film</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
