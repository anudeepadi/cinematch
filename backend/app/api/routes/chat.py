"""
Chat endpoint for conversational movie recommendations.
"""

import asyncio
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.movie import Movie
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

# Timeout for AI API calls (in seconds)
AI_TIMEOUT = 45


class ChatContext(BaseModel):
    mood: Optional[str] = None
    watchingWith: Optional[str] = None
    recentRecommendations: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    message: str
    model: str  # 'claude', 'openai', 'gemini'
    context: Optional[ChatContext] = None


class MovieSuggestion(BaseModel):
    title: str
    year: Optional[int] = None
    poster_url: Optional[str] = None
    movie_id: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    model: str
    movie_suggestions: Optional[List[MovieSuggestion]] = None


def _build_system_prompt(context: Optional[ChatContext]) -> str:
    """Build system prompt with context"""
    base = """You are a friendly movie recommendation assistant. Help users discover movies based on their preferences, mood, and what they're looking for.

When recommending movies:
1. Provide 2-5 specific movie recommendations when asked
2. Explain briefly why each movie might appeal to the user
3. Consider the user's mood and viewing context
4. Be conversational and helpful

IMPORTANT: When you recommend specific movies, you MUST include a JSON block at the END of your response with the movie details in this exact format:
```json
[{"title": "Movie Title", "year": 2020}, {"title": "Another Movie", "year": 2019}]
```

Only include the JSON block if you're actually recommending specific movies."""

    if context:
        additions = []
        if context.mood:
            additions.append(f"The user is currently in a {context.mood} mood.")
        if context.watchingWith:
            additions.append(f"They are watching {context.watchingWith}.")
        if context.recentRecommendations:
            recent = ", ".join(r.get("title", "") for r in context.recentRecommendations[:3])
            additions.append(f"Recently recommended: {recent}")

        if additions:
            base += "\n\nCURRENT CONTEXT:\n" + "\n".join(additions)

    return base


async def _get_claude_response(message: str, context: Optional[ChatContext]) -> tuple[str, List[dict]]:
    """Get response from Claude"""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    system_prompt = _build_system_prompt(context)

    def make_request():
        return client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        )

    response = await asyncio.wait_for(
        asyncio.to_thread(make_request),
        timeout=AI_TIMEOUT
    )

    return response.content[0].text, []


async def _get_openai_response(message: str, context: Optional[ChatContext]) -> tuple[str, List[dict]]:
    """Get response from OpenAI GPT"""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    system_prompt = _build_system_prompt(context)

    def make_request():
        return client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )

    response = await asyncio.wait_for(
        asyncio.to_thread(make_request),
        timeout=AI_TIMEOUT
    )

    return response.choices[0].message.content, []


async def _get_gemini_response(message: str, context: Optional[ChatContext]) -> tuple[str, List[dict]]:
    """Get response from Google Gemini"""
    import google.generativeai as genai

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    system_prompt = _build_system_prompt(context)

    def make_request():
        return model.generate_content(f"{system_prompt}\n\nUser: {message}")

    response = await asyncio.wait_for(
        asyncio.to_thread(make_request),
        timeout=AI_TIMEOUT
    )

    return response.text, []


def _extract_movie_suggestions(response_text: str) -> List[dict]:
    """Extract movie suggestions from response text"""
    suggestions = []

    # Look for JSON block in response
    try:
        json_start = response_text.find('```json')
        if json_start >= 0:
            json_end = response_text.find('```', json_start + 7)
            if json_end > json_start:
                json_str = response_text[json_start + 7:json_end].strip()
                movies = json.loads(json_str)
                for movie in movies:
                    suggestions.append({
                        "title": movie.get("title", ""),
                        "year": movie.get("year")
                    })
    except (json.JSONDecodeError, ValueError):
        pass

    # Also try to find raw JSON array
    if not suggestions:
        try:
            json_start = response_text.rfind('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                movies = json.loads(json_str)
                if isinstance(movies, list) and len(movies) > 0 and isinstance(movies[0], dict):
                    for movie in movies:
                        if "title" in movie:
                            suggestions.append({
                                "title": movie.get("title", ""),
                                "year": movie.get("year")
                            })
        except (json.JSONDecodeError, ValueError):
            pass

    return suggestions


async def _lookup_movies(
    suggestions: List[dict],
    db: AsyncSession
) -> List[MovieSuggestion]:
    """Look up movies in database to get poster URLs"""
    results = []

    for suggestion in suggestions[:5]:  # Limit to 5
        title = suggestion.get("title", "")
        year = suggestion.get("year")

        # Try to find in database
        stmt = select(Movie).where(Movie.title.ilike(f"%{title}%"))
        if year:
            stmt = stmt.where(Movie.release_year == year)
        stmt = stmt.limit(1)

        result = await db.execute(stmt)
        movie = result.scalar_one_or_none()

        if movie:
            results.append(MovieSuggestion(
                title=movie.title,
                year=movie.release_year,
                poster_url=movie.poster_url or (f"https://image.tmdb.org/t/p/w200{movie.poster_path}" if movie.poster_path else None),
                movie_id=movie.id
            ))
        else:
            results.append(MovieSuggestion(
                title=title,
                year=year
            ))

    return results


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the AI for movie recommendations"""

    # Check if the selected model is available
    model_available = {
        "claude": bool(settings.anthropic_api_key),
        "openai": bool(settings.openai_api_key),
        "gemini": bool(settings.google_api_key)
    }

    if not model_available.get(request.model):
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model} is not available. Please select a different model."
        )

    try:
        # Get response from selected model
        if request.model == "claude":
            response_text, _ = await _get_claude_response(request.message, request.context)
        elif request.model == "openai":
            response_text, _ = await _get_openai_response(request.message, request.context)
        elif request.model == "gemini":
            response_text, _ = await _get_gemini_response(request.message, request.context)
        else:
            raise HTTPException(status_code=400, detail="Invalid model selection")

        # Extract movie suggestions from response
        suggestions = _extract_movie_suggestions(response_text)

        # Look up movies in database
        movie_suggestions = await _lookup_movies(suggestions, db)

        # Clean response text (remove JSON block)
        clean_response = response_text
        json_start = clean_response.find('```json')
        if json_start >= 0:
            json_end = clean_response.find('```', json_start + 7)
            if json_end > json_start:
                clean_response = clean_response[:json_start].strip() + clean_response[json_end + 3:].strip()

        return ChatResponse(
            message=clean_response.strip(),
            model=request.model,
            movie_suggestions=movie_suggestions if movie_suggestions else None
        )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Request to {request.model} timed out. Please try again."
        )
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with {request.model}. Please try again."
        )
