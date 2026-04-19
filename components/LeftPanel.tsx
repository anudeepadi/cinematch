import React, { useState } from 'react';
import { Movie } from '../types';
import { VIBE_PRESETS, VibePreset } from '../constants';

interface LeftPanelProps {
  movie: Movie | null;
  onSearch: (mood: string) => void;
  onPresetClick: (preset: VibePreset) => void;
  isLoading: boolean;
  isLoadingDetails: boolean;
}

function formatRuntime(minutes: number): string {
  if (!minutes) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export const LeftPanel: React.FC<LeftPanelProps> = ({ movie, onSearch, onPresetClick, isLoading, isLoadingDetails }) => {
  const [mood, setMood] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mood.trim()) {
      onSearch(mood);
    }
  };

  const handlePreset = (preset: VibePreset) => {
    setMood(preset.label);
    onPresetClick(preset);
  };

  return (
    <div className="h-full w-full bg-grid flex flex-col border-r border-white/10 relative">
      {/* Top Section: Header & Movie Info - Scrollable */}
      <div className="flex-1 overflow-y-auto p-6 md:p-14 custom-scrollbar">
        <div className="w-full max-w-2xl">
          <h1 className="text-3xl font-black font-sans tracking-tighter mb-12 text-white sticky top-0">cineverse</h1>

          {movie ? (
            <div className="animate-fade-in pb-4">
              {/* Title */}
              <h2 className="text-3xl md:text-5xl lg:text-6xl font-serif-display font-black leading-[0.9] mb-8 text-white uppercase tracking-[-0.04em] shadow-black drop-shadow-lg break-words">
                {movie.title}
              </h2>

              {/* Metadata Grid */}
              <div className="grid grid-cols-3 w-full border-t border-b border-white/20 mb-8">
                <div className="border-r border-white/20 py-3 md:py-4 px-2 md:px-4 flex flex-col justify-center">
                  <span className="block text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-1">Year</span>
                  <span className="text-lg md:text-2xl font-bold font-mono-display">{movie.year}</span>
                </div>
                <div className="border-r border-white/20 py-3 md:py-4 px-2 md:px-4 flex flex-col justify-center">
                  <span className="block text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-1">Lang</span>
                  <span className="text-lg md:text-2xl font-bold font-mono-display">{movie.language}</span>
                </div>
                <div className="py-3 md:py-4 px-2 md:px-4 flex flex-col justify-center">
                  <span className="block text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-1">Rating</span>
                  <div className="flex items-baseline">
                    <span className="text-lg md:text-2xl font-bold font-mono-display">{movie.rating}</span>
                    <span className="text-[10px] md:text-xs text-gray-600 font-mono-display ml-1">/10</span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="font-mono-display text-xs md:text-sm leading-6 md:leading-7 text-gray-300 mb-8 max-w-lg border-b border-white/10 pb-6 tracking-tight">
                {movie.description}
              </p>

              {/* Tagline */}
              {isLoadingDetails ? (
                <div className="border-l-[1px] border-white/30 pl-6 py-1 mb-8">
                  <div className="h-6 w-3/4 bg-white/5 animate-pulse rounded" />
                </div>
              ) : movie.tagline ? (
                <div className="border-l-[1px] border-white pl-6 py-1 italic font-serif-display text-xl md:text-3xl text-gray-200 leading-tight tracking-tight opacity-90 mb-8">
                  "{movie.tagline}"
                </div>
              ) : null}

              {/* Vibe Check: Runtime + Genre Tags */}
              {isLoadingDetails ? (
                <div className="mb-8">
                  <div className="text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-3">Vibe Check</div>
                  <div className="flex gap-2 flex-wrap">
                    <div className="h-7 w-16 bg-white/5 animate-pulse rounded" />
                    <div className="h-7 w-20 bg-white/5 animate-pulse rounded" />
                    <div className="h-7 w-24 bg-white/5 animate-pulse rounded" />
                  </div>
                </div>
              ) : (movie.runtime || (movie.genres && movie.genres.length > 0)) ? (
                <div className="mb-8">
                  <div className="text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-3">Vibe Check</div>
                  <div className="flex gap-2 flex-wrap items-center">
                    {movie.runtime ? (
                      <span className="border border-white/30 px-3 py-1 text-xs font-mono-display text-gray-300 uppercase tracking-wider">
                        {formatRuntime(movie.runtime)}
                      </span>
                    ) : null}
                    {movie.genres.map(g => (
                      <span key={g.id} className="border border-white/20 px-3 py-1 text-[10px] font-mono-display text-gray-400 uppercase tracking-wider">
                        {g.name}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Creative Team: Director + Cast */}
              {isLoadingDetails ? (
                <div className="mb-8">
                  <div className="text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-3">Creative Team</div>
                  <div className="space-y-2">
                    <div className="h-4 w-40 bg-white/5 animate-pulse rounded" />
                    <div className="h-4 w-56 bg-white/5 animate-pulse rounded" />
                  </div>
                </div>
              ) : (movie.director || (movie.cast && movie.cast.length > 0)) ? (
                <div className="mb-8">
                  <div className="text-[10px] text-gray-500 font-mono-display uppercase tracking-widest mb-3">Creative Team</div>
                  {movie.director && (
                    <div className="mb-2">
                      <span className="text-[10px] text-gray-600 font-mono-display uppercase tracking-widest mr-2">Dir.</span>
                      <span className="text-sm font-bold text-white font-mono-display">{movie.director}</span>
                    </div>
                  )}
                  {movie.cast && movie.cast.length > 0 && (
                    <div>
                      <span className="text-[10px] text-gray-600 font-mono-display uppercase tracking-widest mr-2">Cast</span>
                      <span className="text-xs text-gray-400 font-mono-display">{movie.cast.join(' · ')}</span>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="flex flex-col items-start justify-center h-40 opacity-50">
              <p className="font-mono-display text-sm uppercase tracking-widest">Select a movie from the archive</p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Section: Search */}
      <div className="z-10 bg-black/80 backdrop-blur-sm p-6 md:p-14 border-t border-white/10 shrink-0">
        <label className="block text-[10px] font-mono-display uppercase tracking-widest text-gray-500 mb-2 md:mb-4">
          Input Vibe Parameters
        </label>

        <form onSubmit={handleSubmit} className="relative mb-4 md:mb-6 max-w-lg">
          <input
            type="text"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            className="w-full bg-transparent border-b border-gray-700 text-white font-mono-display py-2 md:py-3 focus:outline-none focus:border-white transition-colors placeholder-gray-800 text-base md:text-lg uppercase tracking-tight"
            placeholder="SEARCH MOVIES, GENRES, OR DESCRIBE A VIBE..."
            disabled={isLoading}
          />
          <button
            type="submit"
            className="absolute right-0 top-2 md:top-4 text-[10px] font-bold uppercase tracking-widest hover:text-white text-gray-600 transition-colors"
          >
            {isLoading ? "PROCESSING..." : "RUN"}
          </button>
        </form>

        <div className="flex gap-2 md:gap-3 flex-wrap">
          {VIBE_PRESETS.map(preset => (
            <button
              key={preset.label}
              onClick={() => handlePreset(preset)}
              className="border-[1px] border-white/20 px-3 py-1 md:px-4 md:py-2 text-[8px] md:text-[10px] uppercase font-bold font-mono-display tracking-widest hover:bg-white hover:text-black transition-all duration-300 text-gray-400 hover:border-white"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
