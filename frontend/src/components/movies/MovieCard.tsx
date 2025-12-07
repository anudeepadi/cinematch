import { motion } from 'framer-motion';
import { Star, Calendar, Clock } from 'lucide-react';
import { Movie } from '../../types';

interface MovieCardProps {
  movie: Movie;
  onClick?: () => void;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/300x450?text=No+Poster';

export function MovieCard({ movie, onClick, size = 'md', showDetails = true }: MovieCardProps) {
  const sizeClasses = {
    sm: 'w-32',
    md: 'w-44',
    lg: 'w-56',
  };

  const posterUrl = movie.poster_url
    || (movie.poster_path ? `${TMDB_IMAGE_BASE}/w500${movie.poster_path}` : PLACEHOLDER_POSTER);

  return (
    <motion.div
      whileHover={{ y: -8, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`${sizeClasses[size]} flex-shrink-0 cursor-pointer group`}
    >
      {/* Poster Container */}
      <div className="relative aspect-[2/3] rounded-xl overflow-hidden shadow-lg">
        {/* Poster Image */}
        <img
          src={posterUrl}
          alt={movie.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          loading="lazy"
        />

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-60 group-hover:opacity-80 transition-opacity" />

        {/* Rating Badge */}
        <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-lg">
          <Star size={12} className="text-amber-400 fill-amber-400" />
          <span className="text-xs font-semibold text-white">{movie.vote_average?.toFixed(1)}</span>
        </div>

        {/* Hover Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileHover={{ opacity: 1, y: 0 }}
          className="absolute inset-x-0 bottom-0 p-3"
        >
          <div className="flex items-center gap-3 text-xs text-zinc-300">
            {movie.release_year && (
              <span className="flex items-center gap-1">
                <Calendar size={10} />
                {movie.release_year}
              </span>
            )}
            {movie.runtime && (
              <span className="flex items-center gap-1">
                <Clock size={10} />
                {movie.runtime}m
              </span>
            )}
          </div>
        </motion.div>

        {/* Glow Effect */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute inset-0 bg-gradient-to-t from-amber-500/20 via-transparent to-transparent" />
        </div>
      </div>

      {/* Title & Details */}
      {showDetails && (
        <div className="mt-3 space-y-1">
          <h3 className="text-sm font-medium text-white line-clamp-1 group-hover:text-amber-400 transition-colors">
            {movie.title}
          </h3>
          {movie.genres && movie.genres.length > 0 && (
            <p className="text-xs text-zinc-500 line-clamp-1">
              {movie.genres.slice(0, 2).map(g => g.name).join(' · ')}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
