import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThumbsUp, ThumbsDown, Eye, EyeOff, Star, Sparkles, RefreshCw, ChevronRight, ChevronLeft } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Button } from '../components/common/Button';
import { moviesApi } from '../api/movies';
import { interactionsApi } from '../api/interactions';
import { Movie } from '../types';
import toast from 'react-hot-toast';

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/400x600?text=No+Poster';

export function TrainTastePage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showRating, setShowRating] = useState(false);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [stats, setStats] = useState({ watched: 0, notSeen: 0, rated: 0 });
  const [page, setPage] = useState(1);
  const [isExiting, setIsExiting] = useState(false);
  const [exitDirection, setExitDirection] = useState<'left' | 'right'>('right');

  const loadMovies = useCallback(async (reset = false) => {
    setLoading(true);
    try {
      const currentPage = reset ? 1 : page;
      const data = await moviesApi.getMovies({
        page: currentPage,
        per_page: 20,
        sort_by: 'popularity',
      });

      const movieList = data.movies || data.items || [];

      if (reset) {
        setMovies(movieList);
        setCurrentIndex(0);
        setPage(1);
      } else {
        setMovies(prev => [...prev, ...movieList]);
      }
    } catch (error) {
      console.error('Failed to load movies:', error);
      toast.error('Failed to load movies');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadMovies(true);
  }, []);

  // Load more movies when running low
  useEffect(() => {
    if (currentIndex >= movies.length - 5 && !loading && movies.length > 0) {
      setPage(prev => prev + 1);
      loadMovies();
    }
  }, [currentIndex, movies.length, loading]);

  const currentMovie = movies[currentIndex];

  const handleWatched = async () => {
    if (!currentMovie) return;
    setShowRating(true);
  };

  const handleNotSeen = async () => {
    if (!currentMovie) return;

    try {
      await interactionsApi.createInteraction({
        movie_id: currentMovie.id,
        interaction_type: 'pass',
      });
      setStats(prev => ({ ...prev, notSeen: prev.notSeen + 1 }));
      goToNext('left');
    } catch (error) {
      console.error('Failed to record interaction:', error);
    }
  };

  const handleRatingSubmit = async (liked: boolean) => {
    if (!currentMovie) return;

    try {
      // Create watched interaction
      await interactionsApi.createInteraction({
        movie_id: currentMovie.id,
        interaction_type: 'watched',
      });

      // If they liked it, also mark as favorite
      if (liked) {
        await interactionsApi.createInteraction({
          movie_id: currentMovie.id,
          interaction_type: 'favorite',
        });
      }

      setStats(prev => ({
        ...prev,
        watched: prev.watched + 1,
        rated: prev.rated + 1
      }));

      toast.success(liked ? 'Great choice!' : 'Got it, noted!');
    } catch (error) {
      console.error('Failed to record interaction:', error);
      toast.error('Failed to save');
    }

    setShowRating(false);
    setSelectedRating(null);
    goToNext('right');
  };

  const goToNext = (direction: 'left' | 'right') => {
    setExitDirection(direction);
    setIsExiting(true);

    setTimeout(() => {
      setCurrentIndex(prev => prev + 1);
      setIsExiting(false);
    }, 300);
  };

  const handleSkip = () => {
    goToNext('right');
  };

  const handleRefresh = () => {
    loadMovies(true);
    setStats({ watched: 0, notSeen: 0, rated: 0 });
  };

  if (loading && movies.length === 0) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-12 h-12 border-3 border-amber-500 border-t-transparent rounded-full mx-auto mb-4"
            />
            <p className="text-zinc-400">Loading movies to train your taste...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 text-sm mb-4">
              <Sparkles size={16} />
              Train Your Algorithm
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Help us learn your taste
            </h1>
            <p className="text-zinc-400 max-w-lg mx-auto">
              Tell us which movies you've watched and whether you liked them.
              The more you rate, the better your recommendations become!
            </p>
          </div>

          {/* Stats */}
          <div className="flex justify-center gap-6 mb-8">
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400">{stats.watched}</div>
              <div className="text-xs text-zinc-500">Watched</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-zinc-400">{stats.notSeen}</div>
              <div className="text-xs text-zinc-500">Haven't Seen</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{stats.rated}</div>
              <div className="text-xs text-zinc-500">Rated</div>
            </div>
          </div>

          {/* Movie Card */}
          {currentMovie ? (
            <div className="relative max-w-md mx-auto">
              <AnimatePresence mode="wait">
                {!isExiting && (
                  <motion.div
                    key={currentMovie.id}
                    initial={{ opacity: 0, x: 100 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{
                      opacity: 0,
                      x: exitDirection === 'left' ? -200 : 200,
                      rotate: exitDirection === 'left' ? -10 : 10
                    }}
                    transition={{ duration: 0.3 }}
                    className="relative"
                  >
                    {/* Movie Card */}
                    <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl">
                      {/* Poster */}
                      <div className="relative aspect-[2/3] overflow-hidden">
                        <img
                          src={currentMovie.poster_url ||
                            (currentMovie.poster_path ? `${TMDB_IMAGE_BASE}/w500${currentMovie.poster_path}` : PLACEHOLDER_POSTER)}
                          alt={currentMovie.title}
                          className="w-full h-full object-cover"
                          onError={(e) => { (e.target as HTMLImageElement).src = PLACEHOLDER_POSTER; }}
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-transparent to-transparent" />

                        {/* Movie info overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-6">
                          <h2 className="text-2xl font-bold text-white mb-2">
                            {currentMovie.title}
                          </h2>
                          <div className="flex items-center gap-4 text-sm text-zinc-300">
                            {currentMovie.release_year && (
                              <span>{currentMovie.release_year}</span>
                            )}
                            {currentMovie.vote_average && (
                              <span className="flex items-center gap-1">
                                <Star size={14} className="text-amber-400 fill-amber-400" />
                                {currentMovie.vote_average.toFixed(1)}
                              </span>
                            )}
                          </div>
                          {currentMovie.genres && currentMovie.genres.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-3">
                              {currentMovie.genres.slice(0, 3).map((genre) => (
                                <span
                                  key={genre.id}
                                  className="px-2 py-1 bg-white/10 backdrop-blur-sm text-white text-xs rounded-full"
                                >
                                  {genre.name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Actions or Rating */}
                      <div className="p-6">
                        <AnimatePresence mode="wait">
                          {!showRating ? (
                            <motion.div
                              key="actions"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                            >
                              <p className="text-center text-zinc-400 mb-4">
                                Have you watched this movie?
                              </p>
                              <div className="flex gap-3">
                                <button
                                  onClick={handleNotSeen}
                                  className="flex-1 flex items-center justify-center gap-2 py-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl transition-colors"
                                >
                                  <EyeOff size={20} />
                                  Haven't Seen
                                </button>
                                <button
                                  onClick={handleWatched}
                                  className="flex-1 flex items-center justify-center gap-2 py-4 bg-amber-500 hover:bg-amber-400 text-white rounded-xl transition-colors font-medium"
                                >
                                  <Eye size={20} />
                                  I've Watched It
                                </button>
                              </div>
                            </motion.div>
                          ) : (
                            <motion.div
                              key="rating"
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -20 }}
                            >
                              <p className="text-center text-zinc-400 mb-4">
                                Did you enjoy it?
                              </p>
                              <div className="flex gap-3">
                                <button
                                  onClick={() => handleRatingSubmit(false)}
                                  className="flex-1 flex items-center justify-center gap-2 py-4 bg-zinc-800 hover:bg-red-500/20 hover:border-red-500 border-2 border-transparent text-zinc-300 hover:text-red-400 rounded-xl transition-all"
                                >
                                  <ThumbsDown size={20} />
                                  Not Really
                                </button>
                                <button
                                  onClick={() => handleRatingSubmit(true)}
                                  className="flex-1 flex items-center justify-center gap-2 py-4 bg-amber-500 hover:bg-green-500 text-white rounded-xl transition-colors font-medium"
                                >
                                  <ThumbsUp size={20} />
                                  Loved It!
                                </button>
                              </div>
                              <button
                                onClick={() => {
                                  setShowRating(false);
                                  goToNext('right');
                                }}
                                className="w-full mt-3 py-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
                              >
                                Skip this one
                              </button>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>

                    {/* Skip button */}
                    {!showRating && (
                      <div className="flex justify-center mt-4">
                        <button
                          onClick={handleSkip}
                          className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
                        >
                          Skip
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Navigation hints */}
              <div className="flex justify-between items-center mt-6 px-4">
                <div className="flex items-center gap-2 text-xs text-zinc-600">
                  <ChevronLeft size={14} />
                  Swipe left = Haven't seen
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-600">
                  Swipe right = Watched
                  <ChevronRight size={14} />
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="w-20 h-20 rounded-full bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles size={32} className="text-amber-500" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Great job!
              </h3>
              <p className="text-zinc-400 max-w-sm mx-auto mb-6">
                You've gone through all the movies. Your recommendations are now more personalized!
              </p>
              <Button onClick={handleRefresh} icon={<RefreshCw size={18} />}>
                Load More Movies
              </Button>
            </div>
          )}

          {/* Progress indicator */}
          <div className="mt-8 text-center">
            <p className="text-sm text-zinc-500">
              Movie {currentIndex + 1} of {movies.length}
              {loading && ' (loading more...)'}
            </p>
          </div>

          {/* Tips */}
          <div className="mt-12 p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
            <h3 className="text-sm font-medium text-zinc-300 mb-3">Tips for better recommendations:</h3>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li className="flex items-start gap-2">
                <span className="text-amber-400">1.</span>
                Be honest about which movies you've actually seen
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-400">2.</span>
                Rate as many movies as you can - more data = better recommendations
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-400">3.</span>
                Come back often to keep training your algorithm
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Layout>
  );
}
