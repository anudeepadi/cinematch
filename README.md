# CineMatch

A movie-discovery prototype with swipe feedback, watchlists, genre onboarding and recommendations for solo or shared viewing. The React interface connects to a FastAPI backend and a TMDB movie catalog.

**Status:** application prototype from December 2025. Content-based, collaborative, cold-start and optional LLM recommendation adapters are implemented in source; no held-out comparison establishes that the ensemble improves recommendations.

## Try the workflow

After setup, create a local account, choose genres and rate a few movies. Open recommendations, save a title to the watchlist, pass on another, then check that your interaction history is retained. Movie data comes from your configured TMDB account; provider-backed explanations/recommendations require your own optional AI keys.

## Backend

```bash
git clone https://github.com/anudeepadi/cinematch.git
cd cinematch/backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create `backend/.env` with your own values (there is no tracked backend `.env.example`):

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./cinematch.db
SECRET_KEY=replace-with-your-own-long-random-secret
TMDB_API_KEY=replace-with-your-own-tmdb-key
FRONTEND_URL=http://localhost:5173
```

Optional AI variables are `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY`. SQLite is the default local database; cloud database integrations are optional.

```bash
python scripts/seed_database.py --quick
uvicorn app.main:app --reload
```

The seeder contacts TMDB. API documentation is at `http://localhost:8000/docs` once running.

## Frontend

In another terminal from the repository root:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

The default development URL is `http://localhost:5173`. The current package declares React 19 and Vite 7; use a compatible Node runtime. Set `VITE_API_URL=http://localhost:8000` for the local API.

## Recommendation design

[Recommender implementations](backend/app/services/recommenders/) include content-based, collaborative and cold-start strategies, optional OpenAI/Claude/Gemini adapters, an ensemble and companion-preference merging. These are strategies to evaluate, not a claim that more models produce better results.

For a meaningful comparison, freeze a catalog and interaction split, compare a popularity/genre baseline, and report ranking quality and cold-start behavior separately. Record provider/model versions and cost for any LLM variant. No provider calls, new evaluation or end-to-end run were performed during this documentation refresh.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [deployment notes](RAILWAY_DEPLOYMENT.md) for implementation details. A recorded swipe/recommendation walkthrough remains to be captured from a configured instance.

## License

MIT (as stated in the original project documentation).
