import apiClient from './client';
import { Movie, MovieDetails, Genre, PaginatedResponse } from '../types';

export const moviesApi = {
  getMovies: async (params?: {
    page?: number;
    size?: number;
    genre_id?: number;
    year_min?: number;
    year_max?: number;
    search?: string;
    sort_by?: string;
  }): Promise<PaginatedResponse<Movie>> => {
    const response = await apiClient.get<PaginatedResponse<Movie>>('/movies/', { params });
    return response.data;
  },

  getMovie: async (id: number): Promise<MovieDetails> => {
    const response = await apiClient.get<MovieDetails>(`/movies/${id}`);
    return response.data;
  },

  getMovieByTmdbId: async (tmdbId: number): Promise<MovieDetails> => {
    const response = await apiClient.get<MovieDetails>(`/movies/tmdb/${tmdbId}`);
    return response.data;
  },

  getGenres: async (): Promise<Genre[]> => {
    const response = await apiClient.get<Genre[]>('/movies/genres');
    return response.data;
  },

  getPopular: async (limit?: number): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/movies/trending', {
      params: { limit: limit || 20 }
    });
    return response.data;
  },

  getTopRated: async (limit?: number): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/movies/top-rated', {
      params: { limit: limit || 20 }
    });
    return response.data;
  },

  searchMovies: async (query: string, limit?: number): Promise<Movie[]> => {
    const response = await apiClient.get<Movie[]>('/movies/search', {
      params: { q: query, limit: limit || 20 }
    });
    return response.data;
  },
};
