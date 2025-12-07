// User types
export interface User {
  id: number;
  email: string;
  username: string;
  profile_image?: string;
  preferred_genres: number[];
  year_range_min: number;
  year_range_max: number;
  mood_scores: Record<string, number>;
  is_onboarded: boolean;
  created_at: string;
}

export interface UserPreferences {
  preferred_genres: number[];
  year_range_min: number;
  year_range_max: number;
  mood_scores: Record<string, number>;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Movie types
export interface Genre {
  id: number;
  tmdb_id: number;
  name: string;
}

export interface Movie {
  id: number;
  tmdb_id: number;
  title: string;
  overview?: string;
  poster_path?: string;
  poster_url?: string;
  backdrop_path?: string;
  backdrop_url?: string;
  release_date?: string;
  release_year?: number;
  vote_average: number;
  vote_count?: number;
  popularity?: number;
  runtime?: number;
  tagline?: string;
  genres: Genre[];
  mood_scores?: Record<string, number>;
}

export interface MovieDetails extends Movie {
  cast?: CastMember[];
  similar_movies?: Movie[];
}

export interface CastMember {
  id: number;
  name: string;
  character: string;
  profile_path?: string;
}

// Interaction types
export type InteractionType = 'pass' | 'watch' | 'watched' | 'like' | 'dislike' | 'favorite' | 'rating';

export interface Interaction {
  id: number;
  user_id: number;
  movie_id: number;
  interaction_type: InteractionType;
  rating?: number;
  created_at: string;
}

export interface CreateInteraction {
  movie_id: number;
  interaction_type: InteractionType;
  rating?: number;
}

// Recommendation types
export interface RecommendationSource {
  model: string;  // "claude", "openai", "gemini", "collaborative", "content_based"
  score: number;
  reasoning?: string;
}

export interface RecommendationResult {
  movie_id: number;
  tmdb_id: number;
  title: string;
  score: number;
  reasoning: string;
  source: string;
  metadata: Record<string, any>;
  movie?: Movie;
}

// Backend recommendation item format
export interface RecommendationItem {
  movie: Movie;
  score: number;
  reasoning: string;
  sources: RecommendationSource[];
  match_factors: Record<string, number>;
}

export interface RecommendationResponse {
  session_id: string;
  recommendations: RecommendationItem[];
  context: {
    mood?: string;
    watching_with?: string;
    companion_id?: number;
    used_companion_preferences: boolean;
    algorithm_weights: Record<string, number>;
  };
  total_candidates: number;
  generated_at: string;
}

export interface RecommendationContext {
  mood?: string;
  watching_with?: string;
  prefer_new_releases?: boolean;
  exclude_movie_ids?: number[];
  companion_preferences?: CompanionPreferences;
}

export interface RecommendationSession {
  session_uuid: string;
  recommendations: RecommendationResult[];
  mood?: string;
  watching_with?: string;
  created_at: string;
}

// Companion types
export interface Companion {
  id: number;
  user_id: number;
  companion_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  nickname?: string;
  companion_user?: User;
  created_at: string;
}

export interface CompanionPreferences {
  preferred_genres: number[];
  year_range_min: number;
  year_range_max: number;
  mood_scores: Record<string, number>;
  disliked_genres?: number[];
}

// Mood types
export interface Mood {
  id: string;
  name: string;
  description: string;
  icon: string;
  gradient: string;
}

export const MOODS: Mood[] = [
  { id: 'excited', name: 'Excited', description: 'Ready for action & thrills', icon: '⚡', gradient: 'from-orange-500 to-red-500' },
  { id: 'relaxed', name: 'Relaxed', description: 'Something easy-going', icon: '😌', gradient: 'from-green-400 to-teal-500' },
  { id: 'thoughtful', name: 'Thoughtful', description: 'Mind-bending stories', icon: '🤔', gradient: 'from-purple-500 to-indigo-500' },
  { id: 'adventurous', name: 'Adventurous', description: 'Epic journeys await', icon: '🗺️', gradient: 'from-blue-500 to-cyan-400' },
  { id: 'romantic', name: 'Romantic', description: 'Love is in the air', icon: '💕', gradient: 'from-pink-500 to-rose-400' },
  { id: 'scared', name: 'Scared', description: 'Bring on the scares', icon: '😱', gradient: 'from-gray-700 to-gray-900' },
  { id: 'nostalgic', name: 'Nostalgic', description: 'Classic vibes', icon: '📼', gradient: 'from-amber-400 to-yellow-500' },
  { id: 'inspired', name: 'Inspired', description: 'Something meaningful', icon: '✨', gradient: 'from-violet-500 to-purple-500' },
];

// Watching context types
export interface WatchingContext {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export const WATCHING_CONTEXTS: WatchingContext[] = [
  { id: 'alone', name: 'Solo', description: 'Just me', icon: '🎧' },
  { id: 'partner', name: 'Partner', description: 'Date night', icon: '💑' },
  { id: 'friends', name: 'Friends', description: 'Movie night', icon: '👯' },
  { id: 'family', name: 'Family', description: 'All ages', icon: '👨‍👩‍👧‍👦' },
];

// API response types
export interface PaginatedResponse<T> {
  movies: T[];  // Backend uses 'movies' field
  items?: T[];  // Alias for compatibility
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}
