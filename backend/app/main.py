from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api.routes import auth, users, movies, interactions, recommendations, companions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered movie recommendation system using multi-model ensemble",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  # Accept both /path and /path/ without redirects
)

# CORS middleware - include both local dev and production URLs
cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    # Railway production URLs (add all variations)
    "https://trustworthy-light-production-3a0c.up.railway.app",
    "https://trustworthy-light-production-1e4e.up.railway.app",
]
# Add production frontend URL if configured
if settings.frontend_url:
    # Handle with and without trailing slash
    url = settings.frontend_url.rstrip("/")
    if url not in cors_origins:
        cors_origins.append(url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.up\.railway\.app",  # Allow all Railway URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(movies.router, prefix="/api/movies", tags=["Movies"])
app.include_router(interactions.router, prefix="/api/interactions", tags=["Interactions"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(companions.router, prefix="/api/companions", tags=["Companions"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/status")
async def api_status():
    """Check API keys and service configuration"""
    from app.services.supabase_service import SupabaseService

    return {
        "status": "running",
        "services": {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "google": bool(settings.google_api_key),
            "tmdb": bool(settings.tmdb_api_key),
            "supabase": SupabaseService.is_configured(),
        },
        "database": "sqlite" if "sqlite" in settings.database_url else "postgresql"
    }
