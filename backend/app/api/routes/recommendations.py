from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationSessionResponse,
    RecommendationSessionListResponse,
    OnboardingQuizResponse,
    OnboardingQuizQuestion,
    OnboardingAnswers
)
from app.api.deps import CurrentUser
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate personalized movie recommendations.

    Uses a multi-model ensemble combining:
    - Collaborative filtering
    - Content-based filtering
    - Claude AI recommendations
    - OpenAI GPT recommendations
    - Gemini recommendations

    Considers user's mood, viewing context, and companion preferences.
    """
    # Import the ensemble recommender service (will be implemented in Phase 3)
    from app.services.recommenders.ensemble import EnsembleRecommender

    recommender = EnsembleRecommender(db)
    return await recommender.generate_recommendations(
        user=current_user,
        request=request
    )


@router.get("/sessions", response_model=RecommendationSessionListResponse)
async def get_recommendation_sessions(
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Get user's recommendation session history"""
    from sqlalchemy import select
    from app.models.recommendation import RecommendationSession

    result = await db.execute(
        select(RecommendationSession)
        .where(RecommendationSession.user_id == current_user.id)
        .order_by(RecommendationSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    return RecommendationSessionListResponse(
        sessions=[RecommendationSessionResponse.model_validate(s) for s in sessions],
        total=len(sessions)
    )


@router.get("/sessions/{session_id}", response_model=RecommendationResponse)
async def get_recommendation_session(
    session_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific recommendation session"""
    from sqlalchemy import select
    from app.models.recommendation import RecommendationSession

    result = await db.execute(
        select(RecommendationSession).where(
            RecommendationSession.session_uuid == session_id,
            RecommendationSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundError("Recommendation session")

    # Convert session to response format
    from app.services.recommenders.ensemble import EnsembleRecommender
    recommender = EnsembleRecommender(db)
    return await recommender.session_to_response(session)


@router.post("/next")
async def get_next_recommendations(
    session_id: str,
    count: int = Query(10, ge=1, le=50),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db)
):
    """Get next batch of recommendations from existing session"""
    from app.services.recommenders.ensemble import EnsembleRecommender

    recommender = EnsembleRecommender(db)
    return await recommender.get_next_batch(
        session_id=session_id,
        user_id=current_user.id,
        count=count
    )


@router.get("/onboarding/quiz", response_model=OnboardingQuizResponse)
async def get_onboarding_quiz(
    db: AsyncSession = Depends(get_db)
):
    """Get the onboarding quiz for new users"""
    from app.services.movie_service import MovieService

    movie_service = MovieService(db)
    genres = await movie_service.get_all_genres()
    movies = await movie_service.get_movies_for_onboarding(10)

    questions = [
        OnboardingQuizQuestion(
            id="genres",
            question="Pick your top 3-5 favorite genres",
            type="multi_select",
            options=[{"id": g.tmdb_id, "name": g.name} for g in genres]
        ),
        OnboardingQuizQuestion(
            id="decade",
            question="Which era of movies do you prefer?",
            type="single_select",
            options=[
                {"id": "classics", "name": "Classic Films (before 1990)"},
                {"id": "90s-2000s", "name": "90s & 2000s"},
                {"id": "modern", "name": "Modern (2010+)"},
                {"id": "all", "name": "I love all eras!"}
            ]
        ),
        OnboardingQuizQuestion(
            id="mood",
            question="What mood are you usually in for movies?",
            type="multi_select",
            options=[
                {"id": "excited", "name": "Action-packed & Exciting"},
                {"id": "relaxed", "name": "Relaxed & Chill"},
                {"id": "thoughtful", "name": "Thoughtful & Deep"},
                {"id": "adventurous", "name": "Adventurous"},
                {"id": "romantic", "name": "Romantic"},
                {"id": "scared", "name": "Ready to be Scared"},
                {"id": "inspired", "name": "Want to be Inspired"}
            ]
        ),
        OnboardingQuizQuestion(
            id="sample_movies",
            question="Rate these popular movies (skip if not seen)",
            type="movie_rating",
            movies=[
                {
                    "id": m.id,
                    "tmdb_id": m.tmdb_id,
                    "title": m.title,
                    "release_year": m.release_year,
                    "vote_average": m.vote_average,
                    "poster_url": m.poster_url,
                    "genres": [{"id": g.tmdb_id, "name": g.name} for g in m.genres]
                }
                for m in movies
            ]
        )
    ]

    return OnboardingQuizResponse(questions=questions)


@router.post("/onboarding/complete")
async def complete_onboarding(
    answers: OnboardingAnswers,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Complete onboarding and generate initial recommendations"""
    from app.services.user_service import UserService
    from app.schemas.user import OnboardingPreferences

    user_service = UserService(db)

    # Convert mood selections to preferences
    mood_mapping = {
        "excited": {"action": 5, "thriller": 4},
        "relaxed": {"comedy": 4, "drama": 3},
        "thoughtful": {"drama": 5, "documentary": 4},
        "adventurous": {"action": 4, "scifi": 4},
        "romantic": {"romance": 5, "drama": 3},
        "scared": {"horror": 5, "thriller": 4},
        "inspired": {"documentary": 4, "drama": 4}
    }

    mood_prefs = {}
    for mood in answers.mood_selections:
        if mood in mood_mapping:
            for key, value in mood_mapping[mood].items():
                mood_prefs[key] = max(mood_prefs.get(key, 3), value)

    # Create preferences
    prefs = OnboardingPreferences(
        preferred_genres=answers.genre_selections,
        year_preference=answers.decade_preference,
        mood_preferences=mood_prefs
    )

    await user_service.process_onboarding(current_user, prefs)

    # Record movie ratings
    if answers.movie_ratings:
        from app.services.interaction_service import InteractionService
        from app.schemas.interaction import WatchHistoryCreate

        interaction_service = InteractionService(db)
        for movie_id, rating in answers.movie_ratings.items():
            await interaction_service.add_to_watch_history(
                current_user.id,
                WatchHistoryCreate(
                    movie_id=int(movie_id),
                    rating=rating,
                    enjoyed=rating >= 7
                )
            )

    return {"status": "completed", "message": "Onboarding complete! You're ready for recommendations."}
