import { motion } from 'framer-motion';
import { Movie } from '../../types';
import { MovieCard } from './MovieCard';

interface MovieGridProps {
  movies: Movie[];
  onMovieClick?: (movie: Movie) => void;
  cardSize?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export function MovieGrid({ movies, onMovieClick, cardSize = 'md', loading = false }: MovieGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="aspect-[2/3] bg-zinc-800 rounded-xl" />
            <div className="mt-3 space-y-2">
              <div className="h-4 bg-zinc-800 rounded w-3/4" />
              <div className="h-3 bg-zinc-800 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (movies.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-20 h-20 rounded-full bg-zinc-800/50 flex items-center justify-center mb-4">
          <span className="text-4xl">🎬</span>
        </div>
        <h3 className="text-lg font-medium text-white mb-2">No movies found</h3>
        <p className="text-zinc-500 max-w-sm">
          Try adjusting your filters or search query to find what you're looking for.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6"
    >
      {movies.map((movie) => (
        <motion.div key={movie.id} variants={item}>
          <MovieCard
            movie={movie}
            size={cardSize}
            onClick={() => onMovieClick?.(movie)}
          />
        </motion.div>
      ))}
    </motion.div>
  );
}
