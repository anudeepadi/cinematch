import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Eye, Trash2, Star, Calendar } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Modal } from '../components/common/Modal';
import { MovieDetail } from '../components/movies';
import { interactionsApi } from '../api/interactions';
import { Movie } from '../types';
import toast from 'react-hot-toast';

type Tab = 'watchlist' | 'watched';

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/200x300?text=No+Poster';

export function WatchlistPage() {
  const [activeTab, setActiveTab] = useState<Tab>('watchlist');
  const [watchlist, setWatchlist] = useState<Movie[]>([]);
  const [watched, setWatched] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [watchlistData, watchedData] = await Promise.all([
        interactionsApi.getWatchlist(),
        interactionsApi.getWatched(),
      ]);
      setWatchlist(watchlistData);
      setWatched(watchedData);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load your movies');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (movieId: number) => {
    try {
      // Find the interaction and delete it
      // For now, we'll just remove from the local list
      if (activeTab === 'watchlist') {
        setWatchlist(prev => prev.filter(m => m.id !== movieId));
      } else {
        setWatched(prev => prev.filter(m => m.id !== movieId));
      }
      toast.success('Removed from list');
    } catch (error) {
      toast.error('Failed to remove');
    }
  };

  const handleMoveToWatched = async (movie: Movie) => {
    try {
      await interactionsApi.createInteraction({
        movie_id: movie.id,
        interaction_type: 'watched',
      });
      setWatchlist(prev => prev.filter(m => m.id !== movie.id));
      setWatched(prev => [movie, ...prev]);
      toast.success('Moved to watched!');
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const movies = activeTab === 'watchlist' ? watchlist : watched;

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">My Movies</h1>
            <p className="text-zinc-400">Keep track of what you want to watch and what you've seen</p>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-8 p-1 bg-zinc-900/50 rounded-xl w-fit">
            <button
              onClick={() => setActiveTab('watchlist')}
              className={`
                flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all
                ${activeTab === 'watchlist'
                  ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/25'
                  : 'text-zinc-400 hover:text-white'}
              `}
            >
              <Heart size={18} />
              Watchlist
              {watchlist.length > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {watchlist.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('watched')}
              className={`
                flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all
                ${activeTab === 'watched'
                  ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/25'
                  : 'text-zinc-400 hover:text-white'}
              `}
            >
              <Eye size={18} />
              Watched
              {watched.length > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {watched.length}
                </span>
              )}
            </button>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-32 bg-zinc-800 rounded-xl" />
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && movies.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-20"
            >
              <div className="w-20 h-20 rounded-full bg-zinc-800/50 flex items-center justify-center mx-auto mb-4">
                {activeTab === 'watchlist' ? (
                  <Heart size={32} className="text-zinc-600" />
                ) : (
                  <Eye size={32} className="text-zinc-600" />
                )}
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                {activeTab === 'watchlist' ? 'Your watchlist is empty' : 'No watched movies yet'}
              </h3>
              <p className="text-zinc-500 max-w-sm mx-auto">
                {activeTab === 'watchlist'
                  ? 'Start adding movies you want to watch from the recommendations or discover page.'
                  : 'Movies you mark as watched will appear here.'}
              </p>
            </motion.div>
          )}

          {/* Movie list */}
          {!loading && movies.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              <AnimatePresence>
                {movies.map((movie, index) => (
                  <motion.div
                    key={movie.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ delay: index * 0.05 }}
                    className="group flex gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-all cursor-pointer"
                    onClick={() => setSelectedMovie(movie)}
                  >
                    {/* Poster */}
                    <div className="w-20 h-30 flex-shrink-0 rounded-lg overflow-hidden">
                      <img
                        src={movie.poster_url
                          || (movie.poster_path ? `${TMDB_IMAGE_BASE}/w200${movie.poster_path}` : PLACEHOLDER_POSTER)}
                        alt={movie.title}
                        className="w-full h-full object-cover"
                      />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-white group-hover:text-amber-400 transition-colors mb-1">
                        {movie.title}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-zinc-500 mb-2">
                        {movie.release_year && (
                          <span className="flex items-center gap-1">
                            <Calendar size={12} />
                            {movie.release_year}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Star size={12} className="text-amber-400" />
                          {movie.vote_average?.toFixed(1)}
                        </span>
                      </div>
                      {movie.genres && movie.genres.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {movie.genres.slice(0, 3).map((genre) => (
                            <span
                              key={genre.id}
                              className="px-2 py-0.5 bg-zinc-800 text-zinc-400 text-xs rounded"
                            >
                              {genre.name}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {activeTab === 'watchlist' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleMoveToWatched(movie);
                          }}
                          className="p-2 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-colors"
                          title="Mark as watched"
                        >
                          <Eye size={18} />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemove(movie.id);
                        }}
                        className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                        title="Remove"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}

          {/* Movie Detail Modal */}
          <Modal
            isOpen={!!selectedMovie}
            onClose={() => setSelectedMovie(null)}
            size="xl"
          >
            {selectedMovie && (
              <MovieDetail
                movie={selectedMovie}
                onClose={() => setSelectedMovie(null)}
                isInWatchlist={watchlist.some(m => m.id === selectedMovie.id)}
                isWatched={watched.some(m => m.id === selectedMovie.id)}
              />
            )}
          </Modal>
        </div>
      </div>
    </Layout>
  );
}
