import apiClient from './client';

export interface ChatRequest {
  message: string;
  model: 'claude' | 'openai' | 'gemini';
  context?: {
    mood?: string | null;
    watchingWith?: string | null;
    recentRecommendations?: Array<{
      title: string;
      movie_id: number;
    }>;
  };
}

export interface MovieSuggestion {
  title: string;
  year?: number;
  poster_url?: string;
  movie_id?: number;
}

export interface ChatResponse {
  message: string;
  model: string;
  movie_suggestions?: MovieSuggestion[];
}

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat/message', request);
    return response.data;
  },
};
