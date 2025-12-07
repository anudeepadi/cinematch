import { useState, useRef } from 'react';
import { motion, useMotionValue, useTransform, PanInfo, AnimatePresence } from 'framer-motion';
import { X, Heart, Eye, Star, Calendar, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { RecommendationResult, Movie } from '../../types';

interface SwipeableMovieProps {
  recommendation: RecommendationResult;
  movie?: Movie;
  onSwipeLeft: () => void;  // Pass
  onSwipeRight: () => void; // Add to watchlist
  onSwipeUp: () => void;    // Mark as watched
  isTop?: boolean;
}

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p';
const PLACEHOLDER_POSTER = 'https://via.placeholder.com/500x750?text=No+Poster';
const SWIPE_THRESHOLD = 100;

export function SwipeableMovie({
  recommendation,
  movie,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  isTop = false,
}: SwipeableMovieProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [exitDirection, setExitDirection] = useState<'left' | 'right' | 'up' | null>(null);
  const constraintsRef = useRef(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  // Rotation based on horizontal drag
  const rotate = useTransform(x, [-300, 0, 300], [-25, 0, 25]);

  // Opacity for action indicators
  const passOpacity = useTransform(x, [-SWIPE_THRESHOLD, 0], [1, 0]);
  const watchlistOpacity = useTransform(x, [0, SWIPE_THRESHOLD], [0, 1]);
  const watchedOpacity = useTransform(y, [-SWIPE_THRESHOLD, 0], [1, 0]);

  // Background color based on swipe direction
  const bgColor = useTransform(
    x,
    [-SWIPE_THRESHOLD, 0, SWIPE_THRESHOLD],
    ['rgba(239, 68, 68, 0.2)', 'rgba(0, 0, 0, 0)', 'rgba(34, 197, 94, 0.2)']
  );

  const handleDragEnd = (_: any, info: PanInfo) => {
    const { offset, velocity } = info;

    // Swipe up - mark as watched
    if (offset.y < -SWIPE_THRESHOLD || (velocity.y < -500 && offset.y < -50)) {
      setExitDirection('up');
      onSwipeUp();
      return;
    }

    // Swipe left - pass
    if (offset.x < -SWIPE_THRESHOLD || (velocity.x < -500 && offset.x < -50)) {
      setExitDirection('left');
      onSwipeLeft();
      return;
    }

    // Swipe right - add to watchlist
    if (offset.x > SWIPE_THRESHOLD || (velocity.x > 500 && offset.x > 50)) {
      setExitDirection('right');
      onSwipeRight();
      return;
    }
  };

  const exitVariants = {
    left: { x: -500, opacity: 0, rotate: -30 },
    right: { x: 500, opacity: 0, rotate: 30 },
    up: { y: -500, opacity: 0 },
  };

  // Use movie from recommendation directly, or from separately fetched prop
  const movieData = movie || recommendation.movie;

  const posterUrl = movieData?.poster_url
    || recommendation.metadata?.poster_url
    || (movieData?.poster_path ? `${TMDB_IMAGE_BASE}/w500${movieData.poster_path}` : null)
    || (recommendation.metadata?.poster_path ? `${TMDB_IMAGE_BASE}/w500${recommendation.metadata.poster_path}` : PLACEHOLDER_POSTER);

  const backdropUrl = movieData?.backdrop_url
    || recommendation.metadata?.backdrop_url
    || (movieData?.backdrop_path ? `${TMDB_IMAGE_BASE}/w1280${movieData.backdrop_path}` : null)
    || (recommendation.metadata?.backdrop_path ? `${TMDB_IMAGE_BASE}/w1280${recommendation.metadata.backdrop_path}` : null);

  const genres = movieData?.genres || recommendation.metadata?.genres || [];

  return (
    <motion.div
      ref={constraintsRef}
      className={`absolute inset-0 ${isTop ? 'z-10' : 'z-0'}`}
      style={{ perspective: 1000 }}
    >
      <motion.div
        drag={isTop}
        dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
        dragElastic={0.9}
        onDragEnd={handleDragEnd}
        style={{ x, y, rotate }}
        animate={exitDirection ? exitVariants[exitDirection] : {}}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      >
        {/* Card */}
        <motion.div
          style={{ backgroundColor: bgColor }}
          className="relative w-full h-full rounded-3xl overflow-hidden shadow-2xl shadow-black/50"
        >
          {/* Background Image */}
          <div className="absolute inset-0">
            {backdropUrl ? (
              <img
                src={backdropUrl}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <img
                src={posterUrl}
                alt=""
                className="w-full h-full object-cover scale-150 blur-sm"
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />
          </div>

          {/* Swipe Indicators */}
          <motion.div
            style={{ opacity: passOpacity }}
            className="absolute top-8 left-8 z-20 px-6 py-3 bg-red-500/90 rounded-xl border-4 border-red-400 transform -rotate-12"
          >
            <span className="text-2xl font-bold text-white tracking-wide">PASS</span>
          </motion.div>

          <motion.div
            style={{ opacity: watchlistOpacity }}
            className="absolute top-8 right-8 z-20 px-6 py-3 bg-green-500/90 rounded-xl border-4 border-green-400 transform rotate-12"
          >
            <span className="text-2xl font-bold text-white tracking-wide">WATCH</span>
          </motion.div>

          <motion.div
            style={{ opacity: watchedOpacity }}
            className="absolute top-8 left-1/2 -translate-x-1/2 z-20 px-6 py-3 bg-amber-500/90 rounded-xl border-4 border-amber-400"
          >
            <span className="text-2xl font-bold text-white tracking-wide">SEEN IT</span>
          </motion.div>

          {/* Content */}
          <div className="absolute inset-x-0 bottom-0 p-6 z-10">
            {/* Rating */}
            <div className="flex items-center gap-2 mb-3">
              <div className="flex items-center gap-1 px-3 py-1.5 bg-black/50 backdrop-blur-sm rounded-full">
                <Star size={16} className="text-amber-400 fill-amber-400" />
                <span className="text-white font-semibold">{movieData?.vote_average?.toFixed(1) || '-'}</span>
              </div>
              {movieData?.release_year && (
                <div className="flex items-center gap-1 px-3 py-1.5 bg-black/50 backdrop-blur-sm rounded-full">
                  <Calendar size={14} className="text-zinc-400" />
                  <span className="text-zinc-300 text-sm">{movieData.release_year}</span>
                </div>
              )}
            </div>

            {/* Title */}
            <h2 className="text-3xl font-bold text-white mb-2 text-shadow">
              {recommendation.title || movieData?.title}
            </h2>

            {/* Genres */}
            {genres.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {(Array.isArray(genres) ? genres.slice(0, 3) : []).map((genre: any, i: number) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-white/10 backdrop-blur-sm text-white text-sm rounded-full"
                  >
                    {typeof genre === 'string' ? genre : genre.name}
                  </span>
                ))}
              </div>
            )}

            {/* AI Reasoning */}
            {recommendation.reasoning && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-gradient-to-r from-amber-500/20 to-orange-500/10 backdrop-blur-sm rounded-xl border border-amber-500/20 mb-4"
              >
                <div className="flex items-center gap-2 text-amber-400 text-sm font-medium mb-1">
                  <Sparkles size={14} />
                  Why you'll love this
                </div>
                <p className="text-white/90 text-sm line-clamp-2">{recommendation.reasoning}</p>
              </motion.div>
            )}

            {/* Expand details button */}
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
            >
              {showDetails ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
              <span className="text-sm">{showDetails ? 'Hide details' : 'Show more'}</span>
            </button>

            {/* Expanded details */}
            <AnimatePresence>
              {showDetails && movieData?.overview && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 overflow-hidden"
                >
                  <p className="text-zinc-300 text-sm leading-relaxed">{movieData.overview}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Source badge */}
          <div className="absolute top-4 right-4 z-10">
            <div className="px-3 py-1.5 bg-black/50 backdrop-blur-sm rounded-full text-xs text-zinc-400">
              via {recommendation.source}
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Action buttons (for tap interaction) */}
      {isTop && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-6 z-20">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onSwipeLeft}
            className="w-16 h-16 rounded-full bg-zinc-900/80 backdrop-blur border border-zinc-700 flex items-center justify-center text-red-400 hover:bg-red-500/20 hover:border-red-500/50 transition-all"
          >
            <X size={28} />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onSwipeUp}
            className="w-14 h-14 rounded-full bg-zinc-900/80 backdrop-blur border border-zinc-700 flex items-center justify-center text-amber-400 hover:bg-amber-500/20 hover:border-amber-500/50 transition-all"
          >
            <Eye size={24} />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onSwipeRight}
            className="w-16 h-16 rounded-full bg-zinc-900/80 backdrop-blur border border-zinc-700 flex items-center justify-center text-green-400 hover:bg-green-500/20 hover:border-green-500/50 transition-all"
          >
            <Heart size={28} />
          </motion.button>
        </div>
      )}
    </motion.div>
  );
}
