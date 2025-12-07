import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAuthStore } from './store/authStore';
import {
  HomePage,
  LoginPage,
  RegisterPage,
  RecommendationsPage,
  DiscoverPage,
  WatchlistPage,
  OnboardingPage,
  ProfilePage,
  TrainTastePage,
} from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Public only route (redirect if authenticated)
function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();

  if (isAuthenticated) {
    // If not onboarded, redirect to onboarding
    if (user && !user.is_onboarded) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to="/recommendations" replace />;
  }

  return <>{children}</>;
}

// Onboarding check route
function OnboardingCheckRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user && !user.is_onboarded) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}

function App() {
  const { fetchUser } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />

          {/* Auth routes (public only) */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <LoginPage />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <RegisterPage />
              </PublicOnlyRoute>
            }
          />

          {/* Onboarding (protected but no onboarding check) */}
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <OnboardingPage />
              </ProtectedRoute>
            }
          />

          {/* Protected routes (with onboarding check) */}
          <Route
            path="/recommendations"
            element={
              <OnboardingCheckRoute>
                <RecommendationsPage />
              </OnboardingCheckRoute>
            }
          />
          <Route
            path="/discover"
            element={
              <OnboardingCheckRoute>
                <DiscoverPage />
              </OnboardingCheckRoute>
            }
          />
          <Route
            path="/watchlist"
            element={
              <OnboardingCheckRoute>
                <WatchlistPage />
              </OnboardingCheckRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <OnboardingCheckRoute>
                <ProfilePage />
              </OnboardingCheckRoute>
            }
          />
          <Route
            path="/train"
            element={
              <OnboardingCheckRoute>
                <TrainTastePage />
              </OnboardingCheckRoute>
            }
          />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* Toast notifications */}
        <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#18181b',
              color: '#fafafa',
              border: '1px solid #27272a',
              borderRadius: '12px',
            },
            success: {
              iconTheme: {
                primary: '#f59e0b',
                secondary: '#18181b',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#18181b',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
