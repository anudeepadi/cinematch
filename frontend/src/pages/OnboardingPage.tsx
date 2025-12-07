import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check, Film, Sparkles } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Button } from '../components/common/Button';
import { useAuthStore } from '../store/authStore';
import { moviesApi } from '../api/movies';
import { usersApi } from '../api/users';
import { recommendationsApi } from '../api/recommendations';
import { Genre, Movie } from '../types';
import toast from 'react-hot-toast';

type Step = 'genres' | 'years' | 'movies' | 'complete';

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/300x450?text=No+Poster';

export function OnboardingPage() {
  const navigate = useNavigate();
  const { setOnboarded } = useAuthStore();
  const [step, setStep] = useState<Step>('genres');
  const [genres, setGenres] = useState<Genre[]>([]);
  const [selectedGenres, setSelectedGenres] = useState<number[]>([]);
  const [yearRange, setYearRange] = useState({ min: 1990, max: 2025 });
  const [onboardingMovies, setOnboardingMovies] = useState<Movie[]>([]);
  const [likedMovies, setLikedMovies] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadGenres();
  }, []);

  useEffect(() => {
    if (step === 'movies') {
      loadOnboardingMovies();
    }
  }, [step]);

  const loadGenres = async () => {
    try {
      const data = await moviesApi.getGenres();
      setGenres(data);
    } catch (error) {
      console.error('Failed to load genres:', error);
    }
  };

  const loadOnboardingMovies = async () => {
    try {
      const data = await recommendationsApi.getOnboardingMovies();
      setOnboardingMovies(data);
    } catch (error) {
      console.error('Failed to load onboarding movies:', error);
      // Fallback to popular movies
      const popular = await moviesApi.getPopular(20);
      setOnboardingMovies(popular);
    }
  };

  const toggleGenre = (genreId: number) => {
    setSelectedGenres(prev =>
      prev.includes(genreId)
        ? prev.filter(id => id !== genreId)
        : [...prev, genreId]
    );
  };

  const toggleMovie = (movieId: number) => {
    setLikedMovies(prev =>
      prev.includes(movieId)
        ? prev.filter(id => id !== movieId)
        : [...prev, movieId]
    );
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      await usersApi.completeOnboarding({
        preferred_genres: selectedGenres,
        year_range_min: yearRange.min,
        year_range_max: yearRange.max,
        mood_scores: {},
      });

      setOnboarded();
      setStep('complete');

      setTimeout(() => {
        navigate('/recommendations');
      }, 2000);
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      toast.error('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  const steps: Step[] = ['genres', 'years', 'movies', 'complete'];
  const currentStepIndex = steps.indexOf(step);

  const canProceed = () => {
    switch (step) {
      case 'genres':
        return selectedGenres.length >= 3;
      case 'years':
        return true;
      case 'movies':
        return likedMovies.length >= 3;
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (step === 'movies') {
      handleComplete();
    } else {
      const nextIndex = currentStepIndex + 1;
      if (nextIndex < steps.length) {
        setStep(steps[nextIndex]);
      }
    }
  };

  const prevStep = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setStep(steps[prevIndex]);
    }
  };

  return (
    <Layout showHeader={false}>
      <div className="min-h-screen flex flex-col">
        {/* Progress bar */}
        <div className="fixed top-0 left-0 right-0 z-50 h-1 bg-zinc-800">
          <motion.div
            className="h-full bg-gradient-to-r from-amber-500 to-orange-500"
            initial={{ width: '0%' }}
            animate={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Logo */}
        <div className="pt-8 px-6">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Film className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-white">Cine</span>
              <span className="text-amber-500">Match</span>
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-center justify-center px-4 py-12">
          <div className="w-full max-w-2xl">
            <AnimatePresence mode="wait">
              {/* Step 1: Genres */}
              {step === 'genres' && (
                <motion.div
                  key="genres"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="text-center">
                    <h1 className="text-3xl font-bold text-white mb-2">What do you love to watch?</h1>
                    <p className="text-zinc-400">Select at least 3 genres you enjoy</p>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {genres.map((genre) => (
                      <motion.button
                        key={genre.id}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => toggleGenre(genre.tmdb_id)}
                        className={`
                          relative p-4 rounded-xl text-left transition-all
                          ${selectedGenres.includes(genre.tmdb_id)
                            ? 'bg-amber-500/20 border-2 border-amber-500'
                            : 'bg-zinc-900/50 border-2 border-zinc-800 hover:border-zinc-700'}
                        `}
                      >
                        <span className={`font-medium ${selectedGenres.includes(genre.tmdb_id) ? 'text-white' : 'text-zinc-300'}`}>
                          {genre.name}
                        </span>
                        {selectedGenres.includes(genre.tmdb_id) && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="absolute top-2 right-2 w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center"
                          >
                            <Check size={12} className="text-white" />
                          </motion.div>
                        )}
                      </motion.button>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Step 2: Years */}
              {step === 'years' && (
                <motion.div
                  key="years"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="text-center">
                    <h1 className="text-3xl font-bold text-white mb-2">When's your sweet spot?</h1>
                    <p className="text-zinc-400">Choose your preferred movie era</p>
                  </div>

                  <div className="space-y-8">
                    <div className="text-center">
                      <span className="text-5xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                        {yearRange.min} - {yearRange.max}
                      </span>
                    </div>

                    <div className="space-y-6 px-4">
                      <div>
                        <label className="block text-sm text-zinc-400 mb-2">From</label>
                        <input
                          type="range"
                          min={1920}
                          max={yearRange.max}
                          value={yearRange.min}
                          onChange={(e) => setYearRange({ ...yearRange, min: Number(e.target.value) })}
                          className="w-full accent-amber-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-zinc-400 mb-2">To</label>
                        <input
                          type="range"
                          min={yearRange.min}
                          max={2025}
                          value={yearRange.max}
                          onChange={(e) => setYearRange({ ...yearRange, max: Number(e.target.value) })}
                          className="w-full accent-amber-500"
                        />
                      </div>
                    </div>

                    <div className="flex justify-center gap-3">
                      {[
                        { label: 'Classic', min: 1920, max: 1980 },
                        { label: '80s & 90s', min: 1980, max: 2000 },
                        { label: 'Modern', min: 2000, max: 2025 },
                        { label: 'All Time', min: 1920, max: 2025 },
                      ].map((preset) => (
                        <button
                          key={preset.label}
                          onClick={() => setYearRange({ min: preset.min, max: preset.max })}
                          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm rounded-lg transition-colors"
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Step 3: Movies */}
              {step === 'movies' && (
                <motion.div
                  key="movies"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="text-center">
                    <h1 className="text-3xl font-bold text-white mb-2">Rate some movies</h1>
                    <p className="text-zinc-400">Select at least 3 movies you've enjoyed</p>
                  </div>

                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
                    {onboardingMovies.map((movie) => (
                      <motion.button
                        key={movie.id}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => toggleMovie(movie.id)}
                        className="relative aspect-[2/3] rounded-xl overflow-hidden"
                      >
                        <img
                          src={movie.poster_url || (movie.poster_path ? `${TMDB_IMAGE_BASE}/w300${movie.poster_path}` : PLACEHOLDER_POSTER)}
                          alt={movie.title}
                          className="w-full h-full object-cover"
                          onError={(e) => { (e.target as HTMLImageElement).src = PLACEHOLDER_POSTER; }}
                        />
                        <div className={`
                          absolute inset-0 transition-all
                          ${likedMovies.includes(movie.id)
                            ? 'bg-amber-500/30 ring-4 ring-amber-500'
                            : 'bg-black/20 hover:bg-black/40'}
                        `} />
                        {likedMovies.includes(movie.id) && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="absolute top-2 right-2 w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center"
                          >
                            <Check size={16} className="text-white" />
                          </motion.div>
                        )}
                      </motion.button>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Step 4: Complete */}
              {step === 'complete' && (
                <motion.div
                  key="complete"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center space-y-6"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: 'spring' }}
                    className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mx-auto shadow-2xl shadow-orange-500/30"
                  >
                    <Sparkles size={40} className="text-white" />
                  </motion.div>

                  <h1 className="text-3xl font-bold text-white">You're all set!</h1>
                  <p className="text-zinc-400 max-w-md mx-auto">
                    We're preparing your personalized movie recommendations. Redirecting you now...
                  </p>

                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                  >
                    <div className="flex justify-center">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full"
                      />
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Navigation */}
        {step !== 'complete' && (
          <div className="sticky bottom-0 p-6 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent">
            <div className="max-w-2xl mx-auto flex items-center justify-between">
              <Button
                variant="ghost"
                onClick={prevStep}
                disabled={currentStepIndex === 0}
                icon={<ArrowLeft size={18} />}
              >
                Back
              </Button>

              <div className="flex gap-2">
                {steps.slice(0, -1).map((s, i) => (
                  <div
                    key={s}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      i <= currentStepIndex ? 'bg-amber-500' : 'bg-zinc-700'
                    }`}
                  />
                ))}
              </div>

              <Button
                onClick={nextStep}
                disabled={!canProceed()}
                isLoading={loading}
                icon={<ArrowRight size={18} />}
                iconPosition="right"
              >
                {step === 'movies' ? 'Finish' : 'Continue'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
