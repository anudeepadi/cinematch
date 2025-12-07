import apiClient from './client';
import {
  RecommendationResult,
  RecommendationContext,
  RecommendationSession,
  RecommendationResponse,
  RecommendationItem,
  Movie
} from '../types';

// Transform backend RecommendationItem to frontend RecommendationResult format
function transformRecommendation(item: RecommendationItem): RecommendationResult {
  return {
    movie_id: item.movie.id,
    tmdb_id: item.movie.tmdb_id,
    title: item.movie.title,
    score: item.score,
    reasoning: item.reasoning,
    source: item.sources.length > 0 ? item.sources[0].model : 'ensemble',
    metadata: {
      match_factors: item.match_factors,
      sources: item.sources,
      poster_url: item.movie.poster_url,
      poster_path: item.movie.poster_path,
    },
    movie: item.movie,
  };
}

export const recommendationsApi = {
  generate: async (context: RecommendationContext, count?: number): Promise<RecommendationResult[]> => {
    const response = await apiClient.post<RecommendationResponse>(
      '/recommendations/generate',
      { ...context, count: count || 10 }
    );
    // Transform backend format to frontend format
    return response.data.recommendations.map(transformRecommendation);
  },

  getSession: async (sessionId: string): Promise<RecommendationSession> => {
    const response = await apiClient.get<RecommendationSession>(
      `/recommendations/sessions/${sessionId}`
    );
    return response.data;
  },

  getSessions: async (limit?: number): Promise<RecommendationSession[]> => {
    const response = await apiClient.get<RecommendationSession[]>(
      '/recommendations/sessions',
      { params: { limit: limit || 10 } }
    );
    return response.data;
  },

  submitFeedback: async (
    sessionId: string,
    movieId: number,
    feedback: 'helpful' | 'not_helpful',
    reason?: string
  ): Promise<void> => {
    await apiClient.post(`/recommendations/sessions/${sessionId}/feedback`, {
      movie_id: movieId,
      feedback,
      reason,
    });
  },

  getOnboardingMovies: async (count?: number): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/movies/onboarding', {
      params: { count: count || 20 }
    });
    return response.data;
  },

  getTrending: async (count?: number): Promise<RecommendationResult[]> => {
    const response = await apiClient.get<RecommendationResult[]>(
      '/recommendations/trending',
      { params: { count: count || 10 } }
    );
    return response.data;
  },
};
