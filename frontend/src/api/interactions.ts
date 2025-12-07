import apiClient from './client';
import { Interaction, CreateInteraction, Movie } from '../types';

interface WatchlistResponse {
  movies: Movie[];
  total: number;
}

export const interactionsApi = {
  createInteraction: async (data: CreateInteraction): Promise<Interaction> => {
    const response = await apiClient.post<Interaction>('/interactions/', data);
    return response.data;
  },

  getHistory: async (params?: {
    interaction_type?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ items: Interaction[]; total: number }> => {
    const response = await apiClient.get('/interactions/history', { params });
    return response.data;
  },

  getWatchlist: async (): Promise<Movie[]> => {
    const response = await apiClient.get<WatchlistResponse>('/interactions/watchlist');
    return response.data.movies || [];
  },

  getWatched: async (): Promise<Movie[]> => {
    const response = await apiClient.get<WatchlistResponse>('/interactions/watched');
    return response.data.movies || [];
  },

  updateRating: async (interactionId: number, rating: number): Promise<Interaction> => {
    const response = await apiClient.patch<Interaction>(
      `/interactions/${interactionId}/rating`,
      { rating }
    );
    return response.data;
  },

  deleteInteraction: async (interactionId: number): Promise<void> => {
    await apiClient.delete(`/interactions/${interactionId}`);
  },
};
