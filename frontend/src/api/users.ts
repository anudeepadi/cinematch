import apiClient from './client';
import { User, UserPreferences } from '../types';

export const usersApi = {
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/users/me');
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch<User>('/users/me', data);
    return response.data;
  },

  updatePreferences: async (preferences: Partial<UserPreferences>): Promise<User> => {
    const response = await apiClient.patch<User>('/users/me/preferences', preferences);
    return response.data;
  },

  completeOnboarding: async (preferences: UserPreferences): Promise<User> => {
    const response = await apiClient.post<User>('/users/me/onboarding', preferences);
    return response.data;
  },

  deleteAccount: async (): Promise<void> => {
    await apiClient.delete('/users/me');
  },
};
