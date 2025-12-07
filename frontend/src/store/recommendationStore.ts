import { create } from 'zustand';
import {
  RecommendationResult,
  RecommendationContext,
  CompanionPreferences,
  Companion,
} from '../types';
import { recommendationsApi } from '../api/recommendations';

interface RecommendationState {
  recommendations: RecommendationResult[];
  currentIndex: number;
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;

  // Context
  mood: string | null;
  watchingWith: string | null;
  selectedCompanion: Companion | null;
  manualCompanionPrefs: CompanionPreferences | null;

  // Actions
  setMood: (mood: string | null) => void;
  setWatchingWith: (context: string | null) => void;
  setCompanion: (companion: Companion | null) => void;
  setManualCompanionPrefs: (prefs: CompanionPreferences | null) => void;

  generateRecommendations: (excludeIds?: number[]) => Promise<void>;
  nextRecommendation: () => void;
  previousRecommendation: () => void;
  removeCurrentRecommendation: () => void;
  resetRecommendations: () => void;
}

export const useRecommendationStore = create<RecommendationState>((set, get) => ({
  recommendations: [],
  currentIndex: 0,
  isLoading: false,
  error: null,
  sessionId: null,

  mood: null,
  watchingWith: null,
  selectedCompanion: null,
  manualCompanionPrefs: null,

  setMood: (mood) => set({ mood }),
  setWatchingWith: (watchingWith) => set({ watchingWith }),
  setCompanion: (companion) => set({ selectedCompanion: companion, manualCompanionPrefs: null }),
  setManualCompanionPrefs: (prefs) => set({ manualCompanionPrefs: prefs, selectedCompanion: null }),

  generateRecommendations: async (excludeIds = []) => {
    const { mood, watchingWith, selectedCompanion, manualCompanionPrefs } = get();

    set({ isLoading: true, error: null });

    try {
      const context: RecommendationContext = {
        mood: mood || undefined,
        watching_with: watchingWith || undefined,
        exclude_movie_ids: excludeIds,
      };

      // Add companion preferences if watching with someone
      if (watchingWith && watchingWith !== 'alone') {
        if (manualCompanionPrefs) {
          context.companion_preferences = manualCompanionPrefs;
        }
        // Note: linked companion preferences are handled server-side
      }

      const recommendations = await recommendationsApi.generate(context, 15);

      set({
        recommendations,
        currentIndex: 0,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.message || 'Failed to generate recommendations',
        isLoading: false,
      });
    }
  },

  nextRecommendation: () => {
    const { currentIndex, recommendations } = get();
    if (currentIndex < recommendations.length - 1) {
      set({ currentIndex: currentIndex + 1 });
    }
  },

  previousRecommendation: () => {
    const { currentIndex } = get();
    if (currentIndex > 0) {
      set({ currentIndex: currentIndex - 1 });
    }
  },

  removeCurrentRecommendation: () => {
    const { recommendations, currentIndex } = get();
    const newRecommendations = [...recommendations];
    newRecommendations.splice(currentIndex, 1);

    set({
      recommendations: newRecommendations,
      currentIndex: Math.min(currentIndex, newRecommendations.length - 1),
    });
  },

  resetRecommendations: () => {
    set({
      recommendations: [],
      currentIndex: 0,
      mood: null,
      watchingWith: null,
      selectedCompanion: null,
      manualCompanionPrefs: null,
      error: null,
    });
  },
}));
