# CineMatch - AI-Powered Movie Recommender

A sophisticated movie recommendation website using a multi-model AI ensemble (Claude + OpenAI + Gemini) combined with traditional ML techniques for highly personalized recommendations.

## Features

- **Hybrid Recommendation System**: Combines collaborative filtering, content-based filtering, and LLM-enhanced recommendations
- **Multi-Model AI Ensemble**: Weighted aggregation from Claude, OpenAI GPT, and Gemini
- **Tinder-Style Swipe Interface**: Swipe right (watchlist), left (pass), or up (watched)
- **Mood-Based Filtering**: Get recommendations based on your current mood
- **Watch Together**: Link companion accounts or input manual preferences for joint viewing
- **Cold-Start Onboarding**: Genre preferences and movie rating quiz for new users
- **Watchlist Management**: Track movies you want to watch and have watched

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with async support
- **SQLite** (dev) / PostgreSQL (prod)
- **JWT Authentication** - Secure token-based auth
- **TMDB API** - Movie data source

### Frontend
- **React 18** + TypeScript
- **Vite** - Fast build tool
- **Tailwind CSS v4** - Utility-first styling
- **Zustand** - State management
- **Framer Motion** - Animations
- **React Router v6** - Routing
- **React Query** - Data fetching

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- TMDB API Key (get one at https://www.themoviedb.org/settings/api)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Seed the database with movies
python scripts/seed_database.py

# Start the server
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
cp .env.example .env

# Start dev server
npm run dev
```

Frontend runs at http://localhost:5173

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./cinematch.db
SECRET_KEY=your-super-secret-key-min-32-chars
TMDB_API_KEY=your-tmdb-api-key
OPENAI_API_KEY=sk-...        # Optional
ANTHROPIC_API_KEY=sk-ant-... # Optional
GOOGLE_API_KEY=...           # Optional
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
movies_recommender/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Security, config
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   │       └── recommenders/  # ML + AI recommenders
│   └── scripts/             # Database seeding
├── frontend/
│   └── src/
│       ├── api/             # API client
│       ├── components/      # React components
│       ├── pages/           # Page components
│       ├── store/           # Zustand stores
│       └── types/           # TypeScript types
└── README.md
```

## Recommendation Algorithm

The system uses a weighted ensemble approach:

1. **Collaborative Filtering** (25%): Based on similar users' preferences
2. **Content-Based** (25%): Based on movie embeddings and similarity
3. **Claude AI** (20%): Nuanced reasoning about preferences
4. **OpenAI GPT** (15%): Broad knowledge base
5. **Google Gemini** (15%): Recency awareness

Results are aggregated using Weighted Borda Count with diversity bonuses.

## License

MIT
