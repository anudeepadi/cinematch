import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, RefreshCw, Sparkles } from 'lucide-react';
import { RecommendationResult, Movie, InteractionType } from '../../types';
import { SwipeableMovie } from './SwipeableMovie';
import { Button } from '../common/Button';
import { interactionsApi } from '../../api/interactions';
import { moviesApi } from '../../api/movies';
import toast from 'react-hot-toast';

interface RecommendationStackProps {
  recommendations: RecommendationResult[];
  isLoading: boolean;
  onRefresh: () => void;
  onComplete: () => void;
}

export function RecommendationStack({
  recommendations,
  isLoading,
  onRefresh,
  onComplete,
}: RecommendationStackProps) {
  const [cards, setCards] = useState<RecommendationResult[]>([]);
  const [movies, setMovies] = useState<Record<number, Movie>>({});
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    setCards(recommendations);
    setCurrentIndex(0);

    // Pre-fetch movie details for better UX
    recommendations.forEach(async (rec) => {
      if (!movies[rec.movie_id]) {
        try {
          const movie = await moviesApi.getMovie(rec.movie_id);
          setMovies(prev => ({ ...prev, [rec.movie_id]: movie }));
        } catch {
          // Ignore errors - we have basic info from recommendation
        }
      }
    });
  }, [recommendations]);

  const handleInteraction = async (type: InteractionType) => {
    const currentCard = cards[currentIndex];
    if (!currentCard) return;

    try {
      await interactionsApi.createInteraction({
        movie_id: currentCard.movie_id,
        interaction_type: type,
      });

      if (type === 'watch') {
        toast.success('Added to watchlist!', { icon: '❤️' });
      } else if (type === 'watched') {
        toast.success('Marked as watched!', { icon: '👀' });
      }
    } catch (error) {
      console.error('Failed to record interaction:', error);
    }

    // Move to next card
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      onComplete();
    }
  };

  const handleSwipeLeft = () => handleInteraction('pass');
  const handleSwipeRight = () => handleInteraction('watch');
  const handleSwipeUp = () => handleInteraction('watched');

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px]">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="mb-4"
        >
          <Sparkles size={48} className="text-amber-500" />
        </motion.div>
        <h3 className="text-xl font-semibold text-white mb-2">Finding your perfect movies...</h3>
        <p className="text-zinc-400 text-center max-w-sm">
          Our AI ensemble is analyzing your preferences across multiple models
        </p>
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] text-center">
        <div className="w-20 h-20 rounded-full bg-zinc-800/50 flex items-center justify-center mb-4">
          <span className="text-4xl">🎬</span>
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">No recommendations yet</h3>
        <p className="text-zinc-400 mb-6 max-w-sm">
          Select your mood and preferences above to get personalized movie recommendations
        </p>
        <Button onClick={onRefresh} icon={<Sparkles size={18} />}>
          Get Recommendations
        </Button>
      </div>
    );
  }

  if (currentIndex >= cards.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-6 shadow-lg shadow-orange-500/30"
        >
          <span className="text-5xl">🎉</span>
        </motion.div>
        <h3 className="text-2xl font-bold text-white mb-2">All caught up!</h3>
        <p className="text-zinc-400 mb-6 max-w-sm">
          You've gone through all recommendations. Want to see more?
        </p>
        <Button onClick={onRefresh} icon={<RefreshCw size={18} />}>
          Load More Recommendations
        </Button>
      </div>
    );
  }

  // Show only top 3 cards for performance
  const visibleCards = cards.slice(currentIndex, currentIndex + 3);

  return (
    <div className="relative h-[600px] w-full max-w-md mx-auto">
      {/* Progress indicator */}
      <div className="absolute -top-8 left-0 right-0 flex items-center gap-2">
        <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-amber-500 to-orange-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <span className="text-sm text-zinc-500">
          {currentIndex + 1}/{cards.length}
        </span>
      </div>

      {/* Card Stack */}
      <div className="relative h-full">
        <AnimatePresence>
          {visibleCards.map((rec, index) => (
            <SwipeableMovie
              key={rec.movie_id}
              recommendation={rec}
              movie={movies[rec.movie_id]}
              onSwipeLeft={handleSwipeLeft}
              onSwipeRight={handleSwipeRight}
              onSwipeUp={handleSwipeUp}
              isTop={index === 0}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Instructions */}
      <div className="absolute -bottom-16 left-0 right-0 flex justify-center gap-8 text-sm text-zinc-500">
        <span className="flex items-center gap-1">
          ← <span className="text-red-400">Pass</span>
        </span>
        <span className="flex items-center gap-1">
          ↑ <span className="text-amber-400">Watched</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="text-green-400">Watchlist</span> →
        </span>
      </div>
    </div>
  );
}
