export interface VibePreset {
  label: string;
  genres: number[];
  keywords?: string;
}

// TMDB genre IDs mapped to mood-based presets
export const VIBE_PRESETS: VibePreset[] = [
  { label: 'JUST HAD A BREAKUP', genres: [10749, 18], keywords: 'heartbreak' },
  { label: 'DYSTOPIAN FUTURE', genres: [878, 53] },
  { label: '90S NOSTALGIA', genres: [35, 18], keywords: '1990s' },
  { label: 'MIND BENDING', genres: [878, 9648] },
  { label: 'COZY ANIMATION', genres: [16, 10751] },
  { label: 'DARK THRILLER', genres: [53, 80] },
];

// TMDB genre ID reference (for Gemini service)
export const TMDB_GENRES: Record<number, string> = {
  28: 'Action',
  12: 'Adventure',
  16: 'Animation',
  35: 'Comedy',
  80: 'Crime',
  99: 'Documentary',
  18: 'Drama',
  10751: 'Family',
  14: 'Fantasy',
  36: 'History',
  27: 'Horror',
  10402: 'Music',
  9648: 'Mystery',
  10749: 'Romance',
  878: 'Science Fiction',
  10770: 'TV Movie',
  53: 'Thriller',
  10752: 'War',
  37: 'Western',
};

export const CYLINDER_CONFIG = {
  POSTER_WIDTH: 3,
  POSTER_HEIGHT: 4.5,
  GAP: 0.05,
  COLUMNS: 20,
  MIN_MOVIES: 40,
};

export const TMDB_POSTER_SIZES = {
  SMALL: 'w185',
  MEDIUM: 'w342',
  LARGE: 'w500',
  ORIGINAL: 'original',
} as const;
