# CineMatch Architecture & Algorithm Documentation

## Overview

CineMatch is an AI-powered movie recommendation system that uses a **multi-model ensemble approach**, combining traditional recommendation algorithms with modern Large Language Models (LLMs) to deliver highly personalized movie suggestions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React 19)                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Pages     │ │   Stores    │ │ API Client  │ │     Components          ││
│  │ - Home      │ │ - authStore │ │ - Axios     │ │ - MovieCard             ││
│  │ - Discover  │ │ - recStore  │ │ - Interceptors│ │ - RecommendationFeed   ││
│  │ - Recommend │ │             │ │             │ │ - Header/Nav            ││
│  │ - Watchlist │ │             │ │             │ │                         ││
│  │ - Profile   │ │             │ │             │ │                         ││
│  │ - TrainTaste│ │             │ │             │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND (FastAPI)                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           API Routes                                     ││
│  │  /api/auth   /api/users   /api/movies   /api/interactions   /api/recs   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Services Layer                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────┐    ││
│  │  │                    EnsembleRecommender                          │    ││
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│    ││
│  │  │  │Content-Based │ │Collaborative │ │     AI Recommenders      ││    ││
│  │  │  │ (Embeddings) │ │ (User-User)  │ │ ┌────────┐ ┌───────────┐ ││    ││
│  │  │  └──────────────┘ └──────────────┘ │ │ Claude │ │  OpenAI   │ ││    ││
│  │  │                                     │ └────────┘ └───────────┘ ││    ││
│  │  │  ┌──────────────┐ ┌──────────────┐ │ ┌────────┐               ││    ││
│  │  │  │ Cold Start   │ │  Companion   │ │ │ Gemini │               ││    ││
│  │  │  │   Handler    │ │   Merger     │ │ └────────┘               ││    ││
│  │  │  └──────────────┘ └──────────────┘ └──────────────────────────┘│    ││
│  │  └─────────────────────────────────────────────────────────────────┘    ││
│  │  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐      ││
│  │  │InteractionService │ │  MovieService     │ │ SupabaseService   │      ││
│  │  └───────────────────┘ └───────────────────┘ └───────────────────┘      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Database Layer                                   ││
│  │            SQLAlchemy (Async) + SQLite/PostgreSQL                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Sync
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (Cloud Storage)                             │
│          users, user_preferences, user_movie_interactions                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Zustand, TanStack Query |
| Backend | FastAPI (Python 3.12), Async SQLAlchemy |
| Database | SQLite (dev), PostgreSQL/Supabase (prod) |
| AI/ML | Claude API, OpenAI GPT-4o-mini, Google Gemini 2.0 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Auth | JWT (7-day expiration) |

---

## Database Schema

### Core Models

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│      User        │     │      Movie       │     │      Genre       │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ id               │     │ id               │     │ id               │
│ email            │     │ tmdb_id          │     │ tmdb_id          │
│ username         │     │ title            │     │ name             │
│ hashed_password  │     │ overview         │     └────────┬─────────┘
│ preferred_genres │     │ release_year     │              │
│ year_range_min   │     │ vote_average     │              │
│ year_range_max   │     │ popularity       │     ┌────────┴─────────┐
│ mood_* (8 fields)│     │ poster_path      │     │   movie_genres   │
│ created_at       │     │ content_embedding│     │  (join table)    │
└────────┬─────────┘     │ mood_scores      │     └──────────────────┘
         │               └────────┬─────────┘
         │                        │
         │    ┌───────────────────┴───────────────────┐
         │    │                                       │
         ▼    ▼                                       ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│  UserMovieInteraction    │              │      WatchHistory        │
├──────────────────────────┤              ├──────────────────────────┤
│ user_id (FK)             │              │ user_id (FK)             │
│ movie_id (FK)            │              │ movie_id (FK)            │
│ interaction_type         │              │ watched_at               │
│ rating                   │              │ rating                   │
│ mood_at_interaction      │              │ enjoyed                  │
│ watching_with            │              │ would_recommend          │
│ created_at               │              │ mood_before/after        │
└──────────────────────────┘              └──────────────────────────┘

┌──────────────────────────┐              ┌──────────────────────────┐
│     UserPreference       │              │  RecommendationSession   │
├──────────────────────────┤              ├──────────────────────────┤
│ user_id (FK)             │              │ session_uuid             │
│ genre_weights (JSON)     │              │ user_id (FK)             │
│ preferred_decades        │              │ mood, watching_with      │
│ total_watched/passed     │              │ recommendations (JSON)   │
│ favorite_count           │              │ algorithm_weights        │
│ preference_embedding     │              │ claude/openai/gemini_recs│
└──────────────────────────┘              └──────────────────────────┘
```

### Interaction Types
- `watch` - User wants to watch (added to watchlist)
- `pass` - User rejected the movie
- `watched` - User has seen the movie
- `favorite` - User favorited the movie
- `like` / `dislike` - Quick preference signals

---

## Recommendation Engine

### Algorithm Flow

```
User Request (mood, context, companion)
            │
            ▼
    ┌───────────────────┐
    │ Build Preferences │ ← From interaction history
    └─────────┬─────────┘
              │
              ▼
    ┌───────────────────┐     ┌─────────────────────┐
    │  Check Cold Start │────►│  ColdStartHandler   │
    │   (< 3 movies?)   │ Yes │  Genre + Popularity │
    └─────────┬─────────┘     └─────────────────────┘
              │ No
              ▼
    ┌───────────────────┐
    │  Companion Mode?  │────► CompanionMerger
    └─────────┬─────────┘      (merge preferences)
              │
              ▼
    ┌───────────────────────────────────────────────────┐
    │            PARALLEL EXECUTION (45s timeout)        │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
    │  │Content-Based│ │Collaborative│ │   Claude    │  │
    │  │  (0.25)     │ │  (0.10-0.30)│ │   (0.20)    │  │
    │  └─────────────┘ └─────────────┘ └─────────────┘  │
    │  ┌─────────────┐ ┌─────────────┐                  │
    │  │   OpenAI    │ │   Gemini    │                  │
    │  │   (0.15)    │ │   (0.15)    │                  │
    │  └─────────────┘ └─────────────┘                  │
    └───────────────────────┬───────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Weighted Borda Count   │
              │     Aggregation         │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │   Final Ranked List     │
              │   + Diversity Bonus     │
              └─────────────────────────┘
```

---

## Individual Recommender Algorithms

### 1. Content-Based Recommender

**How it works:**
1. Each movie has a 384-dimensional embedding vector (from sentence-transformers)
2. Compute user's preference vector = weighted average of liked movie embeddings
3. Score candidates by cosine similarity to user preference
4. Apply mood and genre boosts

**Formula:**
```
final_score = similarity × 0.6 + mood_boost × 0.2 + genre_boost × 0.2
```

**Weight:** 0.25 (constant)

---

### 2. Collaborative Filtering Recommender

**How it works:**
1. Find similar users (Jaccard similarity on liked movies)
2. Get movies liked by similar users (not seen by current user)
3. Score by weighted average of ratings

**Formula:**
```
similarity = |intersection| / |union|
movie_score = popularity × 0.4 + weighted_avg_rating × 0.6
```

**Weight:** 0.10 (< 10 history) → 0.30 (20+ history)

---

### 3. AI Recommenders (Claude, OpenAI, Gemini)

**How it works:**
1. Get 100 candidate movies (filtered, popularity-sorted)
2. Build prompt with user preferences + 50 movie summaries
3. Ask AI to select top N as JSON with scores and reasoning
4. Parse and validate response

**Prompt Structure:**
```
You are a movie recommendation expert. Select the best {count} movies.

User context:
- Preferred genres: Action, Sci-Fi
- Current mood: excited
- Watching with: friends
- Year preference: 1990-2024

Available movies:
ID:1 | Inception (2010) | Sci-Fi, Action | 8.4/10
ID:2 | The Matrix (1999) | Sci-Fi, Action | 8.7/10
...

Respond with ONLY a JSON array:
[{"id": movie_id, "score": 0.0-1.0, "reasoning": "brief explanation"}]
```

**Weights:** Claude (0.20), OpenAI (0.15), Gemini (0.15)

---

### 4. Cold Start Handler

**Trigger:** User has < 3 movie interactions

**Strategy:**
1. Get popular, highly-rated movies (vote_count ≥ 1000, rating ≥ 7.0)
2. Filter by user's stated genre preferences
3. Ensure genre diversity (max 3 per genre)
4. Score by popularity × mood_match

---

### 5. Companion Merger (Watch Together)

**Purpose:** Merge two users' preferences for joint viewing

**Merge Rules:**
- **Genres:** Intersection (both must like); fallback to top 3 each
- **Year Range:** Union (widest range)
- **Excluded Genres:** Union (veto power)
- **Mood Scores:** Average, unless either rates < 2 (veto)

**Compatibility Score:**
```
compatibility = genre_overlap × 0.6 + mood_similarity × 0.4
```

---

## Ensemble Aggregation: Weighted Borda Count

### Algorithm

1. **Collect Results:** Each recommender returns ranked list of movies
2. **Assign Borda Points:** For movie at rank i in list of n:
   ```
   borda_points = (n - i) / n
   ```
3. **Weight by Source:**
   ```
   weighted_score = borda_points × source_weight
   ```
4. **Diversity Bonus:** Movies from multiple sources get bonus:
   ```
   bonus = min(unique_sources × 0.05, 0.25)
   ```
5. **Final Score:** Normalize to 0-1, sort descending

### Dynamic Source Weights

| Source | Weight (Low History) | Weight (High History) |
|--------|---------------------|----------------------|
| Content-Based | 0.25 | 0.25 |
| Collaborative | 0.10 | 0.30 |
| Claude | 0.20 | 0.20 |
| OpenAI | 0.15 | 0.15 |
| Gemini | 0.15 | 0.15 |

---

## API Endpoints

### Authentication
```
POST /api/auth/register    - Create new user
POST /api/auth/login       - Get JWT token
GET  /api/auth/me          - Get current user
```

### Movies
```
GET  /api/movies/          - List movies (paginated)
GET  /api/movies/{id}      - Get movie details
GET  /api/movies/genres    - List all genres
GET  /api/movies/search    - Search movies
```

### Interactions
```
POST /api/interactions/           - Create interaction (watch/pass/favorite)
GET  /api/interactions/watchlist  - Get user's watchlist
GET  /api/interactions/watched    - Get watched movies
GET  /api/interactions/favorites  - Get favorites
DELETE /api/interactions/watchlist/{id} - Remove from watchlist
```

### Recommendations
```
POST /api/recommendations/generate  - Generate new recommendations
GET  /api/recommendations/session/{id} - Get session details
```

### Companions
```
GET  /api/companions/        - List companions
POST /api/companions/link    - Send link request
POST /api/companions/accept  - Accept link request
```

---

## Data Flow: User Interaction

```
User swipes right on movie
         │
         ▼
Frontend: interactionsApi.createInteraction({
    movie_id: 123,
    interaction_type: 'watch'
})
         │
         ▼
Backend: POST /api/interactions/
         │
         ├──► SQLite: INSERT INTO user_movie_interactions
         │
         ├──► Update UserPreference.genre_weights
         │
         └──► Sync to Supabase (async, fire-and-forget)
                    │
                    ▼
              Supabase: user_movie_interactions table
```

---

## Learning & Adaptation

### Genre Weight Updates

When user interacts with a movie:
```python
weight_delta = {
    'watch': +0.1,
    'favorite': +0.2,
    'watched': +0.1,
    'pass': -0.1
}

for genre in movie.genres:
    current = genre_weights.get(genre.id, 0.5)
    new_weight = clamp(current + delta, 0.0, 1.0)
    genre_weights[genre.id] = new_weight
```

### Preference Statistics
- `total_watched`: Count of watched movies
- `total_passed`: Count of passed movies
- `favorite_count`: Count of favorites
- `avg_rating`: Average user rating

---

## Performance Optimizations

1. **Parallel Recommender Execution:** All 5 recommenders run concurrently
2. **Timeout Protection:** 30s per AI call, 45s total ensemble
3. **Caching:** User preference embedding cached per session
4. **Eager Loading:** SQLAlchemy selectinload for relationships
5. **Async I/O:** All database and API calls are async

---

## Failure Handling

| Scenario | Handling |
|----------|----------|
| AI API timeout | Returns empty list, other sources continue |
| AI API error | Logged, returns empty list |
| No similar users | Falls back to popularity-based |
| Cold start | Uses ColdStartHandler |
| All recommenders fail | Returns popularity-based fallback |

---

## Environment Variables

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./cinematch.db

# JWT Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

# TMDB
TMDB_API_KEY=...

# Supabase (optional cloud sync)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=...
SUPABASE_SECRET_KEY=...
```

---

## Future Improvements

1. **Real-time Collaborative Filtering:** Use matrix factorization (SVD)
2. **Sequence-aware Recommendations:** Consider watch order
3. **Contextual Bandits:** Explore/exploit balance
4. **A/B Testing Framework:** Compare algorithm variants
5. **Explanation Quality:** Better reasoning from AI models
6. **Social Features:** Friend recommendations, shared watchlists

---

## Running the Application

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Database Seeding
```bash
cd backend
python scripts/seed_database.py      # Fetch movies from TMDB
python scripts/generate_embeddings.py # Generate movie embeddings
```

---

*Last updated: December 2025*
