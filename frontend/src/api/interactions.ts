import apiClient from './client';
import { Interaction, CreateInteraction, Movie } from '../types';

export const interactionsApi = {
  createInteraction: async (data: CreateInteraction): Promise<Interaction> => {
    const response = await apiClient.post<Interaction>('/interactions/', data);
    return response.data;
  },

  getHistory: async (params?: {
    interaction_type?: string;
    page?: number;
    size?: number;
  }): Promise<{ items: Interaction[]; total: number }> => {
    const response = await apiClient.get('/interactions/history', { params });
    return response.data;
  },

  getWatchlist: async (): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/interactions/watchlist');
    return response.data;
  },

  getWatched: async (): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/interactions/watched');
    return response.data;
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
