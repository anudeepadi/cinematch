import apiClient from './client';
import { Companion, CompanionPreferences } from '../types';

export const companionsApi = {
  sendRequest: async (companionEmail: string, nickname?: string): Promise<Companion> => {
    const response = await apiClient.post<Companion>('/companions/request', {
      companion_email: companionEmail,
      nickname,
    });
    return response.data;
  },

  acceptRequest: async (linkId: number): Promise<Companion> => {
    const response = await apiClient.post<Companion>(`/companions/${linkId}/accept`);
    return response.data;
  },

  rejectRequest: async (linkId: number): Promise<void> => {
    await apiClient.post(`/companions/${linkId}/reject`);
  },

  getCompanions: async (): Promise<Companion[]> => {
    const response = await apiClient.get<Companion[]>('/companions/');
    return response.data;
  },

  getPendingRequests: async (): Promise<Companion[]> => {
    const response = await apiClient.get<Companion[]>('/companions/pending');
    return response.data;
  },

  removeCompanion: async (linkId: number): Promise<void> => {
    await apiClient.delete(`/companions/${linkId}`);
  },

  getCompanionPreferences: async (companionId: number): Promise<CompanionPreferences> => {
    const response = await apiClient.get<CompanionPreferences>(
      `/companions/${companionId}/preferences`
    );
    return response.data;
  },
};
