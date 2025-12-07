import { motion } from 'framer-motion';
import { Star, Calendar, Clock, Plus, Check, Heart, X, ExternalLink } from 'lucide-react';
import { Movie } from '../../types';
import { Button } from '../common/Button';

interface MovieDetailProps {
  movie: Movie;
  onClose?: () => void;
  onAddToWatchlist?: () => void;
  onMarkWatched?: () => void;
  isInWatchlist?: boolean;
  isWatched?: boolean;
  reasoning?: string;
  source?: string;
}

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/500x750?text=No+Poster';

export function MovieDetail({
  movie,
  onClose,
  onAddToWatchlist,
  onMarkWatched,
  isInWatchlist = false,
  isWatched = false,
  reasoning,
  source,
}: MovieDetailProps) {
  const backdropUrl = movie.backdrop_url
    || (movie.backdrop_path ? `${TMDB_IMAGE_BASE}/w1280${movie.backdrop_path}` : null);

  const posterUrl = movie.poster_url
    || (movie.poster_path ? `${TMDB_IMAGE_BASE}/w500${movie.poster_path}` : PLACEHOLDER_POSTER);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="relative"
    >
      {/* Close button */}
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
        >
          <X size={24} />
        </button>
      )}

      {/* Backdrop */}
      <div className="relative h-64 sm:h-80 -mx-6 -mt-6 overflow-hidden">
        {backdropUrl ? (
          <>
            <img
              src={backdropUrl}
              alt=""
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/60 to-transparent" />
          </>
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-zinc-900" />
        )}

        {/* Rating overlay */}
        <div className="absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 bg-black/60 backdrop-blur-sm rounded-xl">
          <Star className="text-amber-400 fill-amber-400" size={20} />
          <span className="text-xl font-bold text-white">{movie.vote_average?.toFixed(1)}</span>
          <span className="text-zinc-400 text-sm">/ 10</span>
        </div>
      </div>

      {/* Content */}
      <div className="relative -mt-20 px-6 pb-6">
        <div className="flex gap-6">
          {/* Poster */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="flex-shrink-0 w-32 sm:w-40"
          >
            <img
              src={posterUrl}
              alt={movie.title}
              className="w-full rounded-xl shadow-2xl shadow-black/50"
            />
          </motion.div>

          {/* Info */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex-1 pt-16 sm:pt-20"
          >
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{movie.title}</h1>

            {movie.tagline && (
              <p className="text-zinc-400 italic mb-4">"{movie.tagline}"</p>
            )}

            {/* Meta info */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-400 mb-4">
              {movie.release_year && (
                <span className="flex items-center gap-1.5">
                  <Calendar size={14} />
                  {movie.release_year}
                </span>
              )}
              {movie.runtime && (
                <span className="flex items-center gap-1.5">
                  <Clock size={14} />
                  {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                </span>
              )}
              <span className="flex items-center gap-1.5">
                {movie.vote_count?.toLocaleString()} votes
              </span>
            </div>

            {/* Genres */}
            {movie.genres && movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {movie.genres.map((genre) => (
                  <span
                    key={genre.id}
                    className="px-3 py-1 bg-amber-500/10 text-amber-400 text-sm rounded-full"
                  >
                    {genre.name}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* AI Reasoning */}
        {reasoning && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl"
          >
            <div className="flex items-center gap-2 text-amber-400 text-sm font-medium mb-2">
              <span className="text-lg">✨</span>
              Why we recommend this
              {source && <span className="text-zinc-500 font-normal">• {source}</span>}
            </div>
            <p className="text-zinc-300">{reasoning}</p>
          </motion.div>
        )}

        {/* Overview */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="mt-6"
        >
          <h2 className="text-lg font-semibold text-white mb-2">Overview</h2>
          <p className="text-zinc-400 leading-relaxed">{movie.overview || 'No overview available.'}</p>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8 flex flex-wrap gap-3"
        >
          {onAddToWatchlist && (
            <Button
              variant={isInWatchlist ? 'secondary' : 'primary'}
              onClick={onAddToWatchlist}
              icon={isInWatchlist ? <Check size={18} /> : <Plus size={18} />}
            >
              {isInWatchlist ? 'In Watchlist' : 'Add to Watchlist'}
            </Button>
          )}

          {onMarkWatched && (
            <Button
              variant={isWatched ? 'secondary' : 'ghost'}
              onClick={onMarkWatched}
              icon={<Heart size={18} className={isWatched ? 'fill-current' : ''} />}
            >
              {isWatched ? 'Watched' : 'Mark as Watched'}
            </Button>
          )}

          <Button
            variant="ghost"
            icon={<ExternalLink size={18} />}
            onClick={() => window.open(`https://www.themoviedb.org/movie/${movie.tmdb_id}`, '_blank')}
          >
            TMDB
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}
