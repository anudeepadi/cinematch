import React, { useState, useEffect, useCallback } from 'react';
import { Scene } from './components/Scene';
import { LeftPanel } from './components/LeftPanel';
import { getVibeRecommendation } from './services/geminiService';
import { fetchPopularMovies, searchMovies, discoverByGenres, fetchFullMovieInfo } from './services/tmdbService';
import { Movie } from './types';
import { VibePreset } from './constants';

const App: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [recommendedIds, setRecommendedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  // Load popular movies on mount
  useEffect(() => {
    const loadInitial = async () => {
      try {
        const [page1, page2] = await Promise.all([
          fetchPopularMovies(1),
          fetchPopularMovies(2),
        ]);
        const allMovies = [...page1, ...page2];
        setMovies(allMovies);
        if (allMovies.length > 0) {
          setSelectedMovie(allMovies[0]);
          loadDetails(allMovies[0]);
        }
      } catch (error) {
        console.error('Failed to load initial movies:', error);
      }
    };
    loadInitial();
  }, []);

  const loadDetails = useCallback(async (movie: Movie) => {
    // Skip if already has details loaded
    if (movie.director || movie.tagline || movie.runtime) return;

    setIsLoadingDetails(true);
    try {
      const details = await fetchFullMovieInfo(Number(movie.id));
      setSelectedMovie(prev => {
        if (prev && prev.id === movie.id) {
          return { ...prev, ...details };
        }
        return prev;
      });
      // Also update in the movies array so re-clicking doesn't refetch
      setMovies(prev => prev.map(m =>
        m.id === movie.id ? { ...m, ...details } : m
      ));
    } catch (error) {
      console.error('Failed to load movie details:', error);
    } finally {
      setIsLoadingDetails(false);
    }
  }, []);

  const handleMovieSelect = useCallback((id: string) => {
    const movie = movies.find(m => m.id === id);
    if (movie) {
      setSelectedMovie(movie);
      loadDetails(movie);
    }
  }, [movies, loadDetails]);

  const handleSearch = useCallback(async (mood: string) => {
    setIsLoading(true);
    setRecommendedIds([]);
    try {
      // First try direct TMDB text search
      let results = await searchMovies(mood);

      // If few results, supplement with AI vibe-based discovery
      if (results.length < 5) {
        const vibe = await getVibeRecommendation(mood);
        const discovered = await discoverByGenres(vibe.genres, vibe.keywords || undefined);
        // Merge and deduplicate
        const existingIds = new Set(results.map(m => m.id));
        const supplemental = discovered.filter(m => !existingIds.has(m.id));
        results = [...results, ...supplemental];
      }

      if (results.length > 0) {
        setMovies(results);
        setSelectedMovie(results[0]);
        loadDetails(results[0]);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, [loadDetails]);

  const handlePresetClick = useCallback(async (preset: VibePreset) => {
    setIsLoading(true);
    setRecommendedIds([]);
    try {
      const results = await discoverByGenres(preset.genres, preset.keywords || undefined);
      if (results.length > 0) {
        setMovies(results);
        setSelectedMovie(results[0]);
        loadDetails(results[0]);
      }
    } catch (error) {
      console.error('Preset search failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, [loadDetails]);

  return (
    <div className="flex flex-col md:flex-row w-full h-screen bg-black overflow-hidden">
      {/* Left Panel */}
      <div className="w-full h-[45%] md:w-[40%] md:h-full relative z-20 shadow-[0_10px_30px_rgba(0,0,0,0.8)] md:shadow-[10px_0_30px_rgba(0,0,0,0.8)]">
        <LeftPanel
          movie={selectedMovie}
          onSearch={handleSearch}
          onPresetClick={handlePresetClick}
          isLoading={isLoading}
          isLoadingDetails={isLoadingDetails}
        />
      </div>

      {/* Right Panel: 3D Scene */}
      <div className="w-full h-[55%] md:w-[60%] md:h-full relative z-10">
        <div className="absolute inset-0">
          <Scene
            movies={movies}
            recommendedIds={recommendedIds}
            selectedId={selectedMovie?.id}
            onMovieSelect={handleMovieSelect}
          />
        </div>
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-t md:bg-gradient-to-l from-transparent via-transparent to-black/80" />
      </div>
    </div>
  );
};

export default App;
