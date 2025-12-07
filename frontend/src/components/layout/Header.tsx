import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Film, Search, Heart, User, LogOut, Menu, X, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../store/authStore';

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navItems = [
    { path: '/discover', label: 'Discover', icon: Search },
    { path: '/recommendations', label: 'For You', icon: Film },
    { path: '/watchlist', label: 'Watchlist', icon: Heart },
    { path: '/train', label: 'Train Taste', icon: Sparkles },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      {/* Backdrop blur layer */}
      <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800/50" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div
              whileHover={{ rotate: 10 }}
              className="relative"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/30">
                <Film className="w-5 h-5 text-white" />
              </div>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 blur-lg opacity-50 group-hover:opacity-70 transition-opacity" />
            </motion.div>
            <span className="text-xl font-bold tracking-tight">
              <span className="text-white">Cine</span>
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">Match</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className="relative px-4 py-2 group"
                  >
                    <span className={`
                      flex items-center gap-2 text-sm font-medium transition-colors
                      ${isActive(item.path) ? 'text-white' : 'text-zinc-400 hover:text-white'}
                    `}>
                      <Icon size={18} />
                      {item.label}
                    </span>
                    {isActive(item.path) && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute bottom-0 left-2 right-2 h-0.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                      />
                    )}
                  </Link>
                );
              })}
            </nav>
          )}

          {/* Right side */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                {/* Profile dropdown */}
                <div className="hidden md:flex items-center gap-2">
                  <Link
                    to="/profile"
                    className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white text-sm font-semibold">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <span className="text-sm text-zinc-300">{user?.username}</span>
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="p-2 rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800/50 transition-colors"
                  >
                    <LogOut size={18} />
                  </button>
                </div>

                {/* Mobile menu button */}
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="md:hidden p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-colors"
                >
                  {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="text-sm text-zinc-400 hover:text-white transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-orange-500 rounded-lg hover:shadow-lg hover:shadow-orange-500/30 transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        {isAuthenticated && (
          <motion.nav
            initial={false}
            animate={{ height: isMobileMenuOpen ? 'auto' : 0, opacity: isMobileMenuOpen ? 1 : 0 }}
            className="md:hidden overflow-hidden"
          >
            <div className="py-4 space-y-1 border-t border-zinc-800/50">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`
                      flex items-center gap-3 px-4 py-3 rounded-xl transition-colors
                      ${isActive(item.path)
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white'}
                    `}
                  >
                    <Icon size={20} />
                    {item.label}
                  </Link>
                );
              })}
              <div className="pt-2 mt-2 border-t border-zinc-800/50">
                <Link
                  to="/profile"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-zinc-400 hover:bg-zinc-800/50 hover:text-white rounded-xl transition-colors"
                >
                  <User size={20} />
                  Profile
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-zinc-400 hover:bg-zinc-800/50 hover:text-white rounded-xl transition-colors"
                >
                  <LogOut size={20} />
                  Sign out
                </button>
              </div>
            </div>
          </motion.nav>
        )}
      </div>
    </header>
  );
}
