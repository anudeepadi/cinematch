import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, UserPlus, ChevronRight, Sliders } from 'lucide-react';
import { WATCHING_CONTEXTS, WatchingContext, Companion, CompanionPreferences, Genre } from '../../types';
import { Button } from '../common/Button';

interface WatchingWithSelectorProps {
  selectedContext: string | null;
  onSelectContext: (context: string | null) => void;
  companions: Companion[];
  selectedCompanion: Companion | null;
  onSelectCompanion: (companion: Companion | null) => void;
  manualPreferences: CompanionPreferences | null;
  onSetManualPreferences: (prefs: CompanionPreferences | null) => void;
  genres: Genre[];
}

export function WatchingWithSelector({
  selectedContext,
  onSelectContext,
  companions,
  selectedCompanion,
  onSelectCompanion,
  manualPreferences,
  onSetManualPreferences,
  genres,
}: WatchingWithSelectorProps) {
  const [showManualPrefs, setShowManualPrefs] = useState(false);

  const handleContextSelect = (contextId: string) => {
    if (selectedContext === contextId) {
      onSelectContext(null);
      onSelectCompanion(null);
      onSetManualPreferences(null);
    } else {
      onSelectContext(contextId);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-white mb-1">Who's watching?</h2>
        <p className="text-zinc-400 text-sm">We'll adjust recommendations based on your viewing party</p>
      </div>

      {/* Context Selection */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {WATCHING_CONTEXTS.map((context, index) => (
          <ContextCard
            key={context.id}
            context={context}
            isSelected={selectedContext === context.id}
            onClick={() => handleContextSelect(context.id)}
            index={index}
          />
        ))}
      </div>

      {/* Companion Options - Show when watching with others */}
      <AnimatePresence>
        {selectedContext && selectedContext !== 'alone' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4"
          >
            <div className="h-px bg-zinc-800" />

            <p className="text-sm text-zinc-400 text-center">
              Help us find movies you'll both enjoy
            </p>

            {/* Linked companions */}
            {companions.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                  <Users size={16} />
                  Linked companions
                </h3>
                <div className="space-y-2">
                  {companions.map((companion) => (
                    <motion.button
                      key={companion.id}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => {
                        onSelectCompanion(selectedCompanion?.id === companion.id ? null : companion);
                        onSetManualPreferences(null);
                        setShowManualPrefs(false);
                      }}
                      className={`
                        w-full flex items-center gap-3 p-3 rounded-xl transition-all
                        ${selectedCompanion?.id === companion.id
                          ? 'bg-amber-500/10 border border-amber-500/30'
                          : 'bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700'}
                      `}
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-semibold">
                        {companion.nickname?.charAt(0) || companion.companion_user?.username?.charAt(0) || '?'}
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-medium text-white">
                          {companion.nickname || companion.companion_user?.username}
                        </p>
                        <p className="text-xs text-zinc-500">Uses their taste profile</p>
                      </div>
                      <ChevronRight size={18} className="text-zinc-500" />
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {/* Manual preferences button */}
            <Button
              variant="secondary"
              className="w-full"
              icon={<Sliders size={18} />}
              onClick={() => {
                setShowManualPrefs(!showManualPrefs);
                onSelectCompanion(null);
              }}
            >
              {showManualPrefs ? 'Hide manual preferences' : 'Enter companion preferences manually'}
            </Button>

            {/* Manual preferences form */}
            <AnimatePresence>
              {showManualPrefs && (
                <ManualPreferencesForm
                  genres={genres}
                  preferences={manualPreferences}
                  onSave={onSetManualPreferences}
                />
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface ContextCardProps {
  context: WatchingContext;
  isSelected: boolean;
  onClick: () => void;
  index: number;
}

function ContextCard({ context, isSelected, onClick, index }: ContextCardProps) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        relative p-4 rounded-2xl text-center transition-all duration-300
        ${isSelected
          ? 'bg-amber-500/10 ring-2 ring-amber-500 shadow-lg shadow-amber-500/20'
          : 'bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700'}
      `}
    >
      <span className="text-3xl mb-2 block">{context.icon}</span>
      <h3 className={`font-semibold mb-0.5 transition-colors ${isSelected ? 'text-white' : 'text-zinc-200'}`}>
        {context.name}
      </h3>
      <p className="text-xs text-zinc-500">{context.description}</p>

      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute top-2 right-2 w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center"
        >
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </motion.div>
      )}
    </motion.button>
  );
}

interface ManualPreferencesFormProps {
  genres: Genre[];
  preferences: CompanionPreferences | null;
  onSave: (prefs: CompanionPreferences) => void;
}

function ManualPreferencesForm({ genres, preferences, onSave }: ManualPreferencesFormProps) {
  const [selectedGenres, setSelectedGenres] = useState<number[]>(preferences?.preferred_genres || []);
  const [yearMin, setYearMin] = useState(preferences?.year_range_min || 1990);
  const [yearMax, setYearMax] = useState(preferences?.year_range_max || 2025);

  const toggleGenre = (genreId: number) => {
    setSelectedGenres(prev =>
      prev.includes(genreId)
        ? prev.filter(id => id !== genreId)
        : [...prev, genreId]
    );
  };

  const handleSave = () => {
    onSave({
      preferred_genres: selectedGenres,
      year_range_min: yearMin,
      year_range_max: yearMax,
      mood_scores: {},
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl space-y-4"
    >
      <div>
        <h4 className="text-sm font-medium text-zinc-300 mb-3">Their preferred genres</h4>
        <div className="flex flex-wrap gap-2">
          {genres.map((genre) => (
            <button
              key={genre.id}
              onClick={() => toggleGenre(genre.tmdb_id)}
              className={`
                px-3 py-1.5 text-sm rounded-full transition-all
                ${selectedGenres.includes(genre.tmdb_id)
                  ? 'bg-amber-500 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}
              `}
            >
              {genre.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-zinc-300 mb-3">Year preference</h4>
        <div className="flex items-center gap-4">
          <input
            type="number"
            value={yearMin}
            onChange={(e) => setYearMin(Number(e.target.value))}
            min={1900}
            max={yearMax}
            className="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-center"
          />
          <span className="text-zinc-500">to</span>
          <input
            type="number"
            value={yearMax}
            onChange={(e) => setYearMax(Number(e.target.value))}
            min={yearMin}
            max={2025}
            className="w-24 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-center"
          />
        </div>
      </div>

      <Button onClick={handleSave} className="w-full">
        Apply preferences
      </Button>
    </motion.div>
  );
}
