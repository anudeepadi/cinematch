import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Film, Check } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import toast from 'react-hot-toast';

export function RegisterForm() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { register, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      await register({ email, username, password });
      toast.success('Account created! Let\'s set up your preferences.');
      navigate('/onboarding');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const features = [
    'AI-powered recommendations',
    'Multi-model ensemble (Claude, GPT, Gemini)',
    'Mood-based discovery',
    'Watch with friends - merged taste profiles',
  ];

  return (
    <div className="min-h-screen flex">
      {/* Left side - Visual */}
      <div className="hidden lg:block lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-600/20 via-red-600/20 to-purple-600/20" />
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=1200)',
            filter: 'brightness(0.3)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-zinc-950 via-transparent to-transparent" />

        <div className="relative z-10 h-full flex flex-col justify-center p-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6 leading-tight">
              Discover movies<br />
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                you'll actually love
              </span>
            </h2>

            <div className="space-y-4 mt-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Check size={14} className="text-amber-400" />
                  </div>
                  <span className="text-zinc-300">{feature}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
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

          <h1 className="text-3xl font-bold text-white mb-2">Create your account</h1>
          <p className="text-zinc-400 mb-8">Start your personalized movie journey</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              icon={<User size={20} />}
              required
            />

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
              placeholder="Create a password"
              icon={<Lock size={20} />}
              required
            />

            <Input
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              icon={<Lock size={20} />}
              required
            />

            <div className="pt-2">
              <Button
                type="submit"
                className="w-full"
                size="lg"
                isLoading={isLoading}
                icon={<ArrowRight size={20} />}
                iconPosition="right"
              >
                Create account
              </Button>
            </div>
          </form>

          <p className="text-center text-zinc-500 mt-8">
            Already have an account?{' '}
            <Link to="/login" className="text-amber-400 hover:text-amber-300 font-medium transition-colors">
              Sign in
            </Link>
          </p>

          <p className="text-center text-xs text-zinc-600 mt-6">
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
