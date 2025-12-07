# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI)
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --reload --port 8000  # Start dev server

# Seed database with TMDB movies
python scripts/seed_database.py

# Generate movie embeddings
python scripts/generate_embeddings.py
```

### Frontend (React + Vite)
```bash
cd frontend
npm run dev      # Start dev server (usually port 5173)
npm run build    # TypeScript check + production build
npm run lint     # ESLint
```

## Architecture Overview

### Backend Structure

The backend uses FastAPI with async SQLAlchemy. Key architectural patterns:

- **API Routes** (`app/api/routes/`): Each domain has its own router (auth, users, movies, interactions, recommendations, companions)
- **Services** (`app/services/`): Business logic separated from routes
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation
- **Models** (`app/models/`): SQLAlchemy ORM models

### Recommendation Engine

The core feature is in `app/services/recommenders/`. Uses an ensemble approach:

1. **EnsembleRecommender** (`ensemble.py`): Orchestrates all recommenders and aggregates results using Weighted Borda Count
2. **ContentBasedRecommender**: Movie embedding similarity
3. **CollaborativeFilteringRecommender**: User-user collaborative filtering
4. **ClaudeRecommender/OpenAIRecommender/GeminiRecommender**: LLM-based recommendations
5. **CompanionMerger**: Merges preferences for "watch together" feature
6. **ColdStartHandler**: New user onboarding recommendations

### Frontend Structure

React 19 + TypeScript with Zustand for state management:

- **API Layer** (`src/api/`): Axios client with interceptors for auth tokens
- **Store** (`src/store/`): Zustand stores (authStore, recommendationStore)
- **Pages**: HomePage, DiscoverPage, RecommendationsPage, WatchlistPage, ProfilePage

## Important Conventions

### API Endpoints
- FastAPI uses `redirect_slashes=False` - endpoints work with or without trailing slashes
- All API routes prefixed with `/api/`
- Backend pagination uses `page` and `per_page` parameters (not `size`)

### Authentication
- JWT tokens stored in localStorage under key `token`
- API client automatically adds `Authorization: Bearer <token>` header
- 401 responses trigger redirect to `/login`

### Database
- SQLite for development (`cinematch.db`)
- Async SQLAlchemy with `aiosqlite` driver
- Models use relationship loading with `selectinload` for eager loading

### CORS
- Backend allows origins: localhost:5173, 3000, 3001, 3002
- When adding new frontend ports, update `app/main.py` CORS configuration
