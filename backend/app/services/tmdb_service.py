import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.movie import Movie, Genre
from app.core.exceptions import ExternalAPIError


class TMDBService:
    """Service for interacting with TMDB API"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = settings.tmdb_api_key
        self.base_url = settings.tmdb_base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _fetch(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to TMDB API"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        default_params = {"api_key": self.api_key, "language": "en-US"}
        if params:
            default_params.update(params)

        try:
            async with session.get(url, params=default_params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(2)
                    return await self._fetch(endpoint, params)
                else:
                    raise ExternalAPIError(
                        "TMDB",
                        f"API returned status {response.status}"
                    )
        except aiohttp.ClientError as e:
            raise ExternalAPIError("TMDB", str(e))

    async def fetch_genres(self) -> List[Dict]:
        """Fetch all movie genres from TMDB"""
        data = await self._fetch("/genre/movie/list")
        return data.get("genres", [])

    async def sync_genres(self) -> int:
        """Sync genres from TMDB to database"""
        genres = await self.fetch_genres()
        count = 0

        for genre_data in genres:
            result = await self.db.execute(
                select(Genre).where(Genre.tmdb_id == genre_data["id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.name = genre_data["name"]
            else:
                genre = Genre(tmdb_id=genre_data["id"], name=genre_data["name"])
                self.db.add(genre)
                count += 1

        await self.db.commit()
        return count

    async def fetch_movie_details(self, tmdb_id: int) -> Dict:
        """Fetch detailed movie information"""
        data = await self._fetch(
            f"/movie/{tmdb_id}",
            params={"append_to_response": "credits,keywords"}
        )
        return data

    async def fetch_popular_movies(self, page: int = 1) -> List[Dict]:
        """Fetch popular movies"""
        data = await self._fetch("/movie/popular", params={"page": page})
        return data.get("results", [])

    async def fetch_top_rated_movies(self, page: int = 1) -> List[Dict]:
        """Fetch top rated movies"""
        data = await self._fetch("/movie/top_rated", params={"page": page})
        return data.get("results", [])

    async def fetch_trending_movies(self, time_window: str = "week") -> List[Dict]:
        """Fetch trending movies"""
        data = await self._fetch(f"/trending/movie/{time_window}")
        return data.get("results", [])

    async def process_movie(self, tmdb_id: int) -> Optional[Movie]:
        """Fetch and store/update a movie"""
        try:
            details = await self.fetch_movie_details(tmdb_id)
        except Exception:
            return None

        # Check if movie exists
        result = await self.db.execute(
            select(Movie).where(Movie.tmdb_id == tmdb_id)
        )
        movie = result.scalar_one_or_none()

        # Extract cast
        cast = []
        credits = details.get("credits", {})
        for actor in credits.get("cast", [])[:10]:
            cast.append({
                "id": actor.get("id"),
                "name": actor.get("name"),
                "character": actor.get("character"),
                "profile_path": actor.get("profile_path")
            })

        # Extract directors
        directors = []
        for crew_member in credits.get("crew", []):
            if crew_member.get("job") == "Director":
                directors.append({
                    "id": crew_member.get("id"),
                    "name": crew_member.get("name")
                })

        # Extract keywords
        keywords = [
            kw.get("name")
            for kw in details.get("keywords", {}).get("keywords", [])
        ]

        # Parse release date
        release_date = None
        release_year = None
        if details.get("release_date"):
            try:
                release_date = datetime.strptime(details["release_date"], "%Y-%m-%d")
                release_year = release_date.year
            except ValueError:
                pass

        # Compute mood scores from genres
        mood_scores = self._compute_mood_scores(details.get("genres", []), keywords)

        if movie:
            # Update existing movie
            movie.title = details.get("title", movie.title)
            movie.original_title = details.get("original_title")
            movie.tagline = details.get("tagline")
            movie.overview = details.get("overview")
            movie.release_date = release_date
            movie.release_year = release_year
            movie.runtime = details.get("runtime")
            movie.vote_average = details.get("vote_average", 0)
            movie.vote_count = details.get("vote_count", 0)
            movie.popularity = details.get("popularity", 0)
            movie.poster_path = details.get("poster_path")
            movie.backdrop_path = details.get("backdrop_path")
            movie.original_language = details.get("original_language", "en")
            movie.cast = cast
            movie.directors = directors
            movie.keywords = keywords
            movie.mood_scores = mood_scores
            movie.is_adult = 1 if details.get("adult") else 0
            movie.status = details.get("status", "Released")
            movie.updated_at = datetime.utcnow()
        else:
            # Create new movie
            imdb_id = details.get("imdb_id")
            if not imdb_id:  # Convert empty string to None
                imdb_id = None
            movie = Movie(
                tmdb_id=tmdb_id,
                imdb_id=imdb_id,
                title=details.get("title", "Unknown"),
                original_title=details.get("original_title"),
                tagline=details.get("tagline"),
                overview=details.get("overview"),
                release_date=release_date,
                release_year=release_year,
                runtime=details.get("runtime"),
                vote_average=details.get("vote_average", 0),
                vote_count=details.get("vote_count", 0),
                popularity=details.get("popularity", 0),
                poster_path=details.get("poster_path"),
                backdrop_path=details.get("backdrop_path"),
                original_language=details.get("original_language", "en"),
                cast=cast,
                directors=directors,
                keywords=keywords,
                mood_scores=mood_scores,
                is_adult=1 if details.get("adult") else 0,
                status=details.get("status", "Released")
            )
            self.db.add(movie)

        # Link genres
        genre_ids = [g["id"] for g in details.get("genres", [])]
        genres_result = await self.db.execute(
            select(Genre).where(Genre.tmdb_id.in_(genre_ids))
        )
        genres = genres_result.scalars().all()
        movie.genres = list(genres)

        await self.db.commit()
        await self.db.refresh(movie)
        return movie

    def _compute_mood_scores(
        self,
        genres: List[Dict],
        keywords: List[str]
    ) -> Dict[str, float]:
        """Compute mood scores based on genres and keywords"""
        # Genre to mood mapping
        genre_mood_map = {
            28: {"action": 1.0, "thriller": 0.5},  # Action
            12: {"action": 0.7, "scifi": 0.3},  # Adventure
            16: {"comedy": 0.5, "drama": 0.3},  # Animation
            35: {"comedy": 1.0},  # Comedy
            80: {"thriller": 0.8, "drama": 0.5},  # Crime
            99: {"documentary": 1.0},  # Documentary
            18: {"drama": 1.0},  # Drama
            10751: {"comedy": 0.5, "drama": 0.3},  # Family
            14: {"scifi": 0.7, "action": 0.3},  # Fantasy
            36: {"drama": 0.8, "documentary": 0.3},  # History
            27: {"horror": 1.0, "thriller": 0.5},  # Horror
            10402: {"drama": 0.5, "romance": 0.3},  # Music
            9648: {"thriller": 0.8, "drama": 0.4},  # Mystery
            10749: {"romance": 1.0, "drama": 0.5},  # Romance
            878: {"scifi": 1.0, "action": 0.4},  # Science Fiction
            10770: {"drama": 0.7},  # TV Movie
            53: {"thriller": 1.0, "action": 0.4},  # Thriller
            10752: {"action": 0.8, "drama": 0.6},  # War
            37: {"action": 0.6, "drama": 0.4},  # Western
        }

        moods = {
            "action": 0.0,
            "comedy": 0.0,
            "drama": 0.0,
            "horror": 0.0,
            "romance": 0.0,
            "scifi": 0.0,
            "thriller": 0.0,
            "documentary": 0.0
        }

        # Add genre contributions
        for genre in genres:
            genre_id = genre.get("id")
            if genre_id in genre_mood_map:
                for mood, score in genre_mood_map[genre_id].items():
                    moods[mood] = max(moods[mood], score)

        # Normalize scores
        max_score = max(moods.values()) if moods.values() else 1
        if max_score > 0:
            moods = {k: round(v / max_score, 2) for k, v in moods.items()}

        return moods

    async def seed_popular_movies(
        self,
        pages: int = 50,
        progress_callback=None
    ) -> int:
        """Seed database with popular movies"""
        count = 0

        for page in range(1, pages + 1):
            movies = await self.fetch_popular_movies(page)

            for movie_data in movies:
                movie = await self.process_movie(movie_data["id"])
                if movie:
                    count += 1

            if progress_callback:
                progress_callback(page, pages, count)

            # Rate limit protection
            await asyncio.sleep(0.25)

        return count

    async def seed_top_rated_movies(self, pages: int = 25) -> int:
        """Seed database with top rated movies"""
        count = 0

        for page in range(1, pages + 1):
            movies = await self.fetch_top_rated_movies(page)

            for movie_data in movies:
                movie = await self.process_movie(movie_data["id"])
                if movie:
                    count += 1

            await asyncio.sleep(0.25)

        return count
