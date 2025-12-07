import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Film, Sparkles, Users, Brain, ArrowRight, Play, Star } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { Layout } from '../components/layout/Layout';
import { Button } from '../components/common/Button';
import { MovieCard } from '../components/movies/MovieCard';
import { moviesApi } from '../api/movies';
import { Movie } from '../types';

export function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [featuredMovies, setFeaturedMovies] = useState<Movie[]>([]);

  useEffect(() => {
    moviesApi.getPopular(8).then(setFeaturedMovies).catch(console.error);
  }, []);

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Ensemble',
      description: 'Claude, GPT-4, and Gemini work together to understand your unique taste',
      gradient: 'from-purple-500 to-indigo-500',
    },
    {
      icon: Users,
      title: 'Watch Together',
      description: 'Find movies you\'ll both love with our taste-merging algorithm',
      gradient: 'from-pink-500 to-rose-500',
    },
    {
      icon: Sparkles,
      title: 'Mood-Based Discovery',
      description: 'Tell us how you\'re feeling, and we\'ll find the perfect film',
      gradient: 'from-amber-500 to-orange-500',
    },
  ];

  return (
    <Layout showHeader={true}>
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-zinc-950/90 to-zinc-950" />
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-red-500/20 rounded-full blur-[150px]" />
        </div>

        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 text-sm mb-8"
            >
              <Sparkles size={16} />
              Powered by Multi-AI Ensemble
            </motion.div>

            {/* Headline */}
            <h1 className="text-5xl sm:text-7xl font-bold mb-6 leading-tight">
              <span className="text-white">Discover movies</span>
              <br />
              <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                you'll actually love
              </span>
            </h1>

            <p className="text-xl text-zinc-400 max-w-2xl mx-auto mb-10">
              Our AI ensemble analyzes your taste, mood, and who you're watching with
              to recommend films that truly resonate.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {isAuthenticated ? (
                <Button
                  size="lg"
                  onClick={() => navigate('/recommendations')}
                  icon={<Play size={20} />}
                >
                  Get Recommendations
                </Button>
              ) : (
                <>
                  <Button
                    size="lg"
                    onClick={() => navigate('/register')}
                    icon={<ArrowRight size={20} />}
                    iconPosition="right"
                  >
                    Start for Free
                  </Button>
                  <Button
                    variant="secondary"
                    size="lg"
                    onClick={() => navigate('/login')}
                  >
                    Sign In
                  </Button>
                </>
              )}
            </div>
          </motion.div>

          {/* Floating movie cards preview */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-16 relative"
          >
            <div className="flex justify-center gap-4 perspective-1000">
              {[0, 1, 2].map((index) => (
                <motion.div
                  key={index}
                  initial={{ rotateY: -15, opacity: 0 }}
                  animate={{ rotateY: 0, opacity: 1 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  className={`
                    w-40 h-60 rounded-xl bg-zinc-800 overflow-hidden shadow-2xl
                    ${index === 1 ? 'scale-110 z-10' : 'opacity-70'}
                  `}
                  style={{
                    transform: `rotateY(${(index - 1) * 5}deg)`,
                  }}
                >
                  {featuredMovies[index] && (
                    <img
                      src={featuredMovies[index].poster_url || `https://image.tmdb.org/t/p/w500${featuredMovies[index].poster_path}`}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Not your average recommendation engine
            </h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              We combine cutting-edge AI with proven algorithms to understand
              what you really want to watch.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="group relative p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700/50 transition-all"
              >
                <div className={`
                  w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient}
                  flex items-center justify-center mb-6
                  shadow-lg group-hover:scale-110 transition-transform
                `}>
                  <feature.icon size={24} className="text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-zinc-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Movies Section */}
      {featuredMovies.length > 0 && (
        <section className="py-24 relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex items-center justify-between mb-10"
            >
              <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">
                  Popular right now
                </h2>
                <p className="text-zinc-400">See what everyone's watching</p>
              </div>
              <Link
                to="/discover"
                className="text-amber-400 hover:text-amber-300 flex items-center gap-2 transition-colors"
              >
                Browse all
                <ArrowRight size={18} />
              </Link>
            </motion.div>

            <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide">
              {featuredMovies.map((movie, index) => (
                <motion.div
                  key={movie.id}
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.05 }}
                >
                  <MovieCard movie={movie} size="lg" />
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="py-24 relative">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-12 rounded-3xl bg-gradient-to-br from-amber-500/10 via-orange-500/10 to-red-500/10 border border-amber-500/20"
          >
            <Film size={48} className="text-amber-500 mx-auto mb-6" />
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to find your next favorite movie?
            </h2>
            <p className="text-zinc-400 mb-8 max-w-xl mx-auto">
              Join thousands of movie lovers who've discovered their perfect films with CineMatch.
            </p>
            {!isAuthenticated && (
              <Button
                size="lg"
                onClick={() => navigate('/register')}
                icon={<Sparkles size={20} />}
              >
                Get Started Free
              </Button>
            )}
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-zinc-800/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-zinc-500">
              <Film size={20} />
              <span>CineMatch</span>
            </div>
            <p className="text-sm text-zinc-600">
              Powered by TMDB. Movie data provided by The Movie Database.
            </p>
          </div>
        </div>
      </footer>
    </Layout>
  );
}
