import { motion } from 'framer-motion';
import { MOODS, Mood } from '../../types';

interface MoodSelectorProps {
  selectedMood: string | null;
  onSelect: (mood: string | null) => void;
}

export function MoodSelector({ selectedMood, onSelect }: MoodSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-white mb-1">How are you feeling?</h2>
        <p className="text-zinc-400 text-sm">Select a mood to get personalized recommendations</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {MOODS.map((mood, index) => (
          <MoodCard
            key={mood.id}
            mood={mood}
            isSelected={selectedMood === mood.id}
            onClick={() => onSelect(selectedMood === mood.id ? null : mood.id)}
            index={index}
          />
        ))}
      </div>
    </div>
  );
}

interface MoodCardProps {
  mood: Mood;
  isSelected: boolean;
  onClick: () => void;
  index: number;
}

function MoodCard({ mood, isSelected, onClick, index }: MoodCardProps) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        relative p-4 rounded-2xl text-left transition-all duration-300 overflow-hidden
        ${isSelected
          ? 'ring-2 ring-amber-500 shadow-lg shadow-amber-500/20'
          : 'hover:ring-1 hover:ring-zinc-700'}
      `}
    >
      {/* Background gradient */}
      <div
        className={`
          absolute inset-0 bg-gradient-to-br ${mood.gradient}
          transition-opacity duration-300
          ${isSelected ? 'opacity-20' : 'opacity-10'}
        `}
      />

      {/* Content */}
      <div className="relative z-10">
        <span className="text-3xl mb-2 block">{mood.icon}</span>
        <h3 className={`font-semibold mb-0.5 transition-colors ${isSelected ? 'text-white' : 'text-zinc-200'}`}>
          {mood.name}
        </h3>
        <p className="text-xs text-zinc-400 line-clamp-1">{mood.description}</p>
      </div>

      {/* Selected indicator */}
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
