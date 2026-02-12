import React, { useState, useEffect } from 'react';
import { Scene } from './components/Scene';
import { LeftPanel } from './components/LeftPanel';
import { getMovieRecommendations } from './services/geminiService';
import { MOVIE_DB } from './constants';
import { Movie } from './types';

const App: React.FC = () => {
  const [recommendedIds, setRecommendedIds] = useState<string[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(MOVIE_DB[0]); // Default to first movie
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (mood: string) => {
    setIsLoading(true);
    try {
      const ids = await getMovieRecommendations(mood);
      setRecommendedIds(ids);
      if (ids.length > 0) {
        // Optionally select the first recommended movie
        const firstMatch = MOVIE_DB.find(m => m.id === ids[0]);
        if (firstMatch) setSelectedMovie(firstMatch);
      }
    } catch (error) {
      console.error("Failed to get recommendations", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMovieSelect = (id: string) => {
    const movie = MOVIE_DB.find(m => m.id === id);
    if (movie) {
      setSelectedMovie(movie);
    }
  };

  return (
    <div className="flex flex-col md:flex-row w-full h-screen bg-black overflow-hidden">
      {/* Left Panel: Mobile: Top 45%, Desktop: Left 40% */}
      <div className="w-full h-[45%] md:w-[40%] md:h-full relative z-20 shadow-[0_10px_30px_rgba(0,0,0,0.8)] md:shadow-[10px_0_30px_rgba(0,0,0,0.8)]">
        <LeftPanel 
          movie={selectedMovie} 
          onSearch={handleSearch} 
          isLoading={isLoading} 
        />
      </div>

      {/* Right Panel: Mobile: Bottom 55%, Desktop: Right 60% - 3D Scene */}
      <div className="w-full h-[55%] md:w-[60%] md:h-full relative z-10">
        <div className="absolute inset-0">
          <Scene 
            recommendedIds={recommendedIds} 
            selectedId={selectedMovie?.id}
            onMovieSelect={handleMovieSelect}
          />
        </div>
        {/* Subtle vignette for the 3D side */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-t md:bg-gradient-to-l from-transparent via-transparent to-black/80" />
      </div>
    </div>
  );
};

export default App;
