import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { MoodSelector, WatchingWithSelector, RecommendationStack } from '../components/recommendations';
import { Button } from '../components/common/Button';
import { useRecommendationStore } from '../store/recommendationStore';
import { moviesApi } from '../api/movies';
import { companionsApi } from '../api/companions';
import { Genre, Companion } from '../types';

export function RecommendationsPage() {
  const [showPreferences, setShowPreferences] = useState(true);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [companions, setCompanions] = useState<Companion[]>([]);
  const [hasGenerated, setHasGenerated] = useState(false);

  const {
    recommendations,
    isLoading,
    mood,
    watchingWith,
    selectedCompanion,
    manualCompanionPrefs,
    setMood,
    setWatchingWith,
    setCompanion,
    setManualCompanionPrefs,
    generateRecommendations,
    resetRecommendations,
  } = useRecommendationStore();

  useEffect(() => {
    // Load genres and companions
    moviesApi.getGenres().then(setGenres).catch(console.error);
    companionsApi.getCompanions().then(comps => {
      setCompanions(comps.filter(c => c.status === 'accepted'));
    }).catch(console.error);
  }, []);

  const handleGenerate = async () => {
    await generateRecommendations();
    setHasGenerated(true);
    setShowPreferences(false);
  };

  const handleRefresh = async () => {
    const excludeIds = recommendations.map(r => r.movie_id);
    await generateRecommendations(excludeIds);
  };

  const handleComplete = () => {
    // All cards swiped
    setShowPreferences(true);
  };

  const handleReset = () => {
    resetRecommendations();
    setHasGenerated(false);
    setShowPreferences(true);
  };

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-3xl sm:text-4xl font-bold text-white mb-2"
            >
              <span className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                For You
              </span>
            </motion.h1>
            <p className="text-zinc-400">
              AI-powered recommendations tailored to your taste
            </p>
          </div>

          {/* Preferences Panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className="w-full flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Settings2 size={20} className="text-zinc-400" />
                <span className="font-medium text-white">Preferences</span>
                {(mood || watchingWith) && (
                  <div className="flex items-center gap-2">
                    {mood && (
                      <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                        {mood}
                      </span>
                    )}
                    {watchingWith && (
                      <span className="px-2 py-0.5 bg-zinc-700 text-zinc-300 text-xs rounded-full">
                        {watchingWith}
                      </span>
                    )}
                  </div>
                )}
              </div>
              {showPreferences ? (
                <ChevronUp size={20} className="text-zinc-400" />
              ) : (
                <ChevronDown size={20} className="text-zinc-400" />
              )}
            </button>

            <AnimatePresence>
              {showPreferences && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-6 bg-zinc-900/30 border border-t-0 border-zinc-800 rounded-b-xl space-y-8">
                    {/* Mood Selector */}
                    <MoodSelector
                      selectedMood={mood}
                      onSelect={setMood}
                    />

                    {/* Watching With Selector */}
                    <WatchingWithSelector
                      selectedContext={watchingWith}
                      onSelectContext={setWatchingWith}
                      companions={companions}
                      selectedCompanion={selectedCompanion}
                      onSelectCompanion={setCompanion}
                      manualPreferences={manualCompanionPrefs}
                      onSetManualPreferences={setManualCompanionPrefs}
                      genres={genres}
                    />

                    {/* Generate Button */}
                    <div className="flex justify-center pt-4">
                      <Button
                        size="lg"
                        onClick={handleGenerate}
                        isLoading={isLoading}
                        icon={<Sparkles size={20} />}
                        className="min-w-[200px]"
                      >
                        {hasGenerated ? 'Update Recommendations' : 'Get Recommendations'}
                      </Button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Recommendation Stack */}
          <div className="relative">
            <RecommendationStack
              recommendations={recommendations}
              isLoading={isLoading}
              onRefresh={handleRefresh}
              onComplete={handleComplete}
            />
          </div>

          {/* Reset button */}
          {hasGenerated && !isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-24 text-center"
            >
              <button
                onClick={handleReset}
                className="text-sm text-zinc-500 hover:text-zinc-400 transition-colors"
              >
                Start over with new preferences
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </Layout>
  );
}
