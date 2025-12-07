-- CineMatch Supabase Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (can optionally link with Supabase Auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id UUID UNIQUE,  -- Optional: links to auth.users if using Supabase Auth
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    preferred_genres JSONB DEFAULT '[]'::jsonb,
    year_range_min INTEGER DEFAULT 1970,
    year_range_max INTEGER DEFAULT 2025,
    preferred_languages JSONB DEFAULT '["en"]'::jsonb,
    mood_action INTEGER DEFAULT 3 CHECK (mood_action >= 1 AND mood_action <= 5),
    mood_comedy INTEGER DEFAULT 3 CHECK (mood_comedy >= 1 AND mood_comedy <= 5),
    mood_drama INTEGER DEFAULT 3 CHECK (mood_drama >= 1 AND mood_drama <= 5),
    mood_horror INTEGER DEFAULT 3 CHECK (mood_horror >= 1 AND mood_horror <= 5),
    mood_romance INTEGER DEFAULT 3 CHECK (mood_romance >= 1 AND mood_romance <= 5),
    mood_scifi INTEGER DEFAULT 3 CHECK (mood_scifi >= 1 AND mood_scifi <= 5),
    mood_thriller INTEGER DEFAULT 3 CHECK (mood_thriller >= 1 AND mood_thriller <= 5),
    mood_documentary INTEGER DEFAULT 3 CHECK (mood_documentary >= 1 AND mood_documentary <= 5),
    watch_alone_preference INTEGER DEFAULT 3 CHECK (watch_alone_preference >= 1 AND watch_alone_preference <= 5),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- User preferences (detailed preferences for recommendations)
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    genre_weights JSONB DEFAULT '{}'::jsonb,
    preferred_decades JSONB DEFAULT '[]'::jsonb,
    new_releases_interest FLOAT DEFAULT 0.5 CHECK (new_releases_interest >= 0 AND new_releases_interest <= 1),
    classics_interest FLOAT DEFAULT 0.5 CHECK (classics_interest >= 0 AND classics_interest <= 1),
    actor_preferences JSONB DEFAULT '{}'::jsonb,
    director_preferences JSONB DEFAULT '{}'::jsonb,
    keyword_preferences JSONB DEFAULT '{}'::jsonb,
    avg_rating FLOAT,
    total_watched INTEGER DEFAULT 0,
    total_passed INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    preference_embedding JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- User movie interactions (watch, pass, rate, favorite)
CREATE TABLE IF NOT EXISTS public.user_movie_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL,
    tmdb_id INTEGER NOT NULL,
    interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('watch', 'watched', 'pass', 'rate', 'favorite', 'like', 'dislike')),
    rating FLOAT CHECK (rating >= 0 AND rating <= 10),
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_interactions_user_movie ON public.user_movie_interactions(user_id, movie_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON public.user_movie_interactions(interaction_type);

-- Recommendation sessions
CREATE TABLE IF NOT EXISTS public.recommendation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_uuid VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mood VARCHAR(50),
    watching_with VARCHAR(50),
    companion_id UUID REFERENCES public.users(id),
    companion_preferences JSONB,
    prefer_new_releases BOOLEAN DEFAULT false,
    prefer_classics BOOLEAN DEFAULT false,
    exclude_genres JSONB DEFAULT '[]'::jsonb,
    algorithm_weights JSONB DEFAULT '{}'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    total_candidates INTEGER DEFAULT 0,
    claude_recommendations JSONB,
    openai_recommendations JSONB,
    gemini_recommendations JSONB,
    collaborative_recommendations JSONB,
    content_based_recommendations JSONB,
    merged_preferences JSONB,
    recommendations_shown INTEGER DEFAULT 0,
    current_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.recommendation_sessions(user_id);

-- Companion links for shared recommendations
CREATE TABLE IF NOT EXISTS public.companion_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    companion_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    nickname VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, companion_id)
);

-- Recommendation feedback
CREATE TABLE IF NOT EXISTS public.recommendation_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.recommendation_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL,
    feedback VARCHAR(20) NOT NULL CHECK (feedback IN ('helpful', 'not_helpful')),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_movie_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companion_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = auth_id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = auth_id);

-- RLS Policies for user_preferences
CREATE POLICY "Users can view own preferences" ON public.user_preferences
    FOR SELECT USING (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

CREATE POLICY "Users can update own preferences" ON public.user_preferences
    FOR ALL USING (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

-- RLS Policies for user_movie_interactions
CREATE POLICY "Users can manage own interactions" ON public.user_movie_interactions
    FOR ALL USING (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

-- RLS Policies for recommendation_sessions
CREATE POLICY "Users can view own sessions" ON public.recommendation_sessions
    FOR SELECT USING (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

CREATE POLICY "Users can create sessions" ON public.recommendation_sessions
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

-- RLS Policies for companion_links
CREATE POLICY "Users can view own companion links" ON public.companion_links
    FOR SELECT USING (
        user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()) OR
        companion_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid())
    );

CREATE POLICY "Users can create companion requests" ON public.companion_links
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

CREATE POLICY "Users can update companion links they're part of" ON public.companion_links
    FOR UPDATE USING (
        user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()) OR
        companion_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid())
    );

-- RLS Policies for recommendation_feedback
CREATE POLICY "Users can manage own feedback" ON public.recommendation_feedback
    FOR ALL USING (user_id IN (SELECT id FROM public.users WHERE auth_id = auth.uid()));

-- OPTIONAL: Function to automatically create user profile on Supabase Auth signup
-- Only run this if you are using Supabase Auth for authentication
-- The app currently uses its own JWT auth, so this trigger is optional
/*
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (auth_id, email, username)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
    );

    -- Also create default preferences
    INSERT INTO public.user_preferences (user_id)
    SELECT id FROM public.users WHERE auth_id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for auto-creating user profile (only if using Supabase Auth)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
*/

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_interactions_updated_at
    BEFORE UPDATE ON public.user_movie_interactions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON public.recommendation_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_companions_updated_at
    BEFORE UPDATE ON public.companion_links
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
