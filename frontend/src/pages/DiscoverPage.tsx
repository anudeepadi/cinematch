import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, X, SlidersHorizontal } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { MovieGrid, MovieDetail } from '../components/movies';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { moviesApi } from '../api/movies';
import { interactionsApi } from '../api/interactions';
import { Movie, Genre } from '../types';
import toast from 'react-hot-toast';

export function DiscoverPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState<number | null>(null);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [yearRange, setYearRange] = useState({ min: 1970, max: 2025 });
  const [sortBy, setSortBy] = useState('popularity');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadGenres();
    loadMovies();
  }, []);

  useEffect(() => {
    setPage(1);
    loadMovies(true);
  }, [selectedGenre, sortBy, yearRange]);

  const loadGenres = async () => {
    try {
      const data = await moviesApi.getGenres();
      setGenres(data);
    } catch (error) {
      console.error('Failed to load genres:', error);
    }
  };

  const loadMovies = async (reset = false) => {
    setLoading(true);
    try {
      const data = await moviesApi.getMovies({
        page: reset ? 1 : page,
        per_page: 24,
        genre_id: selectedGenre || undefined,
        year_min: yearRange.min,
        year_max: yearRange.max,
        sort_by: sortBy,
      });

      const movieList = data.movies || data.items || [];
      if (reset) {
        setMovies(movieList);
      } else {
        setMovies(prev => [...prev, ...movieList]);
      }
      setHasMore(data.page < data.pages);
    } catch (error) {
      console.error('Failed to load movies:', error);
      toast.error('Failed to load movies');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadMovies(true);
      return;
    }

    setLoading(true);
    try {
      const data = await moviesApi.searchMovies(searchQuery, 50);
      setMovies(data);
      setHasMore(false);
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!selectedMovie) return;
    try {
      await interactionsApi.createInteraction({
        movie_id: selectedMovie.id,
        interaction_type: 'watch',
      });
      toast.success('Added to watchlist!');
    } catch (error) {
      toast.error('Failed to add to watchlist');
    }
  };

  const handleMarkWatched = async () => {
    if (!selectedMovie) return;
    try {
      await interactionsApi.createInteraction({
        movie_id: selectedMovie.id,
        interaction_type: 'watched',
      });
      toast.success('Marked as watched!');
    } catch (error) {
      toast.error('Failed to mark as watched');
    }
  };

  const loadMore = async () => {
    const nextPage = page + 1;
    setPage(nextPage);
    setLoading(true);
    try {
      const data = await moviesApi.getMovies({
        page: nextPage,
        per_page: 24,
        genre_id: selectedGenre || undefined,
        year_min: yearRange.min,
        year_max: yearRange.max,
        sort_by: sortBy,
      });

      const movieList = data.movies || data.items || [];
      setMovies(prev => [...prev, ...movieList]);
      setHasMore(data.page < data.pages);
    } catch (error) {
      console.error('Failed to load more movies:', error);
      toast.error('Failed to load more movies');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Discover</h1>
            <p className="text-zinc-400">Explore our collection of movies</p>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            {/* Search */}
            <div className="flex-1 relative">
              <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search movies..."
                className="w-full pl-12 pr-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500/50 transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    loadMovies(true);
                  }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white"
                >
                  <X size={18} />
                </button>
              )}
            </div>

            {/* Filter button */}
            <Button
              variant="secondary"
              onClick={() => setShowFilters(!showFilters)}
              icon={<SlidersHorizontal size={18} />}
            >
              Filters
            </Button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl"
            >
              {/* Genre filters */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-400 mb-3">Genres</h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedGenre(null)}
                    className={`
                      px-4 py-2 rounded-lg text-sm transition-all
                      ${!selectedGenre
                        ? 'bg-amber-500 text-white'
                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}
                    `}
                  >
                    All
                  </button>
                  {genres.map((genre) => (
                    <button
                      key={genre.id}
                      onClick={() => setSelectedGenre(genre.tmdb_id)}
                      className={`
                        px-4 py-2 rounded-lg text-sm transition-all
                        ${selectedGenre === genre.tmdb_id
                          ? 'bg-amber-500 text-white'
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}
                      `}
                    >
                      {genre.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Year range */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-400 mb-3">Year Range</h3>
                <div className="flex items-center gap-4">
                  <input
                    type="number"
                    value={yearRange.min}
                    onChange={(e) => setYearRange({ ...yearRange, min: Number(e.target.value) })}
                    min={1900}
                    max={yearRange.max}
                    className="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-center"
                  />
                  <span className="text-zinc-500">to</span>
                  <input
                    type="number"
                    value={yearRange.max}
                    onChange={(e) => setYearRange({ ...yearRange, max: Number(e.target.value) })}
                    min={yearRange.min}
                    max={2025}
                    className="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-center"
                  />
                </div>
              </div>

              {/* Sort */}
              <div>
                <h3 className="text-sm font-medium text-zinc-400 mb-3">Sort By</h3>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                >
                  <option value="popularity">Popularity</option>
                  <option value="vote_average">Rating</option>
                  <option value="release_date">Release Date</option>
                  <option value="title">Title</option>
                </select>
              </div>
            </motion.div>
          )}

          {/* Movie Grid */}
          <MovieGrid
            movies={movies}
            onMovieClick={setSelectedMovie}
            loading={loading && movies.length === 0}
          />

          {/* Load More */}
          {hasMore && movies.length > 0 && (
            <div className="mt-12 text-center">
              <Button
                variant="secondary"
                onClick={loadMore}
                isLoading={loading}
              >
                Load More
              </Button>
            </div>
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
                onAddToWatchlist={handleAddToWatchlist}
                onMarkWatched={handleMarkWatched}
              />
            )}
          </Modal>
        </div>
      </div>
    </Layout>
  );
}
