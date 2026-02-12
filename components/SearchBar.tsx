import React, { useState } from 'react';

interface SearchBarProps {
  onSearch: (mood: string) => void;
  isLoading: boolean;
  recommendationsCount: number;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading, recommendationsCount }) => {
  const [mood, setMood] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mood.trim()) {
      onSearch(mood);
    }
  };

  return (
    <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 w-full max-w-xl px-4 z-10">
      <div className="bg-black/60 backdrop-blur-md border border-white/10 p-6 rounded-2xl shadow-2xl">
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600 mb-2 text-center">
          Vibe Search
        </h1>
        <p className="text-gray-400 text-sm text-center mb-6">
          Describe your mood (e.g., "Neon dystopian future", "Cozy sunday afternoon")
        </p>
        
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            placeholder="How are you feeling today?"
            className="w-full bg-white/5 border border-white/20 text-white px-5 py-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all placeholder-gray-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !mood.trim()}
            className="absolute right-2 top-2 bottom-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 rounded-lg font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center min-w-[100px]"
          >
            {isLoading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              "Find"
            )}
          </button>
        </form>

        {recommendationsCount > 0 && !isLoading && (
          <div className="mt-4 text-center">
            <span className="inline-block bg-green-500/20 text-green-400 text-xs px-3 py-1 rounded-full border border-green-500/30">
              Found {recommendationsCount} movies matching your vibe
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
