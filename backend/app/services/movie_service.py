from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.models.movie import Movie, Genre
from app.schemas.movie import MovieSearchQuery


class MovieService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_movie(self, movie_id: int) -> Optional[Movie]:
        """Get a movie by ID with all relationships"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id == movie_id)
        )
        return result.scalar_one_or_none()

    async def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[Movie]:
        """Get a movie by TMDB ID"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.tmdb_id == tmdb_id)
        )
        return result.scalar_one_or_none()

    async def search_movies(
        self,
        query: MovieSearchQuery
    ) -> Tuple[List[Movie], int]:
        """Search and filter movies with pagination"""
        stmt = select(Movie).options(selectinload(Movie.genres))

        # Text search
        if query.q:
            search_term = f"%{query.q}%"
            stmt = stmt.where(
                or_(
                    Movie.title.ilike(search_term),
                    Movie.original_title.ilike(search_term),
                    Movie.overview.ilike(search_term)
                )
            )

        # Genre filter
        if query.genres:
            stmt = stmt.join(Movie.genres).where(Genre.tmdb_id.in_(query.genres))

        # Year range
        if query.year_min:
            stmt = stmt.where(Movie.release_year >= query.year_min)
        if query.year_max:
            stmt = stmt.where(Movie.release_year <= query.year_max)

        # Minimum rating
        if query.min_rating:
            stmt = stmt.where(Movie.vote_average >= query.min_rating)

        # Sorting
        sort_column = getattr(Movie, query.sort_by, Movie.popularity)
        if query.sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        offset = (query.page - 1) * query.per_page
        stmt = stmt.offset(offset).limit(query.per_page)

        result = await self.db.execute(stmt)
        movies = result.scalars().unique().all()

        return list(movies), total

    async def get_trending_movies(self, limit: int = 20) -> List[Movie]:
        """Get trending movies based on popularity"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .order_by(Movie.popularity.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get_top_rated_movies(self, limit: int = 20, min_votes: int = 100) -> List[Movie]:
        """Get top rated movies with minimum vote threshold"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.vote_count >= min_votes)
            .order_by(Movie.vote_average.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get_movies_by_genre(
        self,
        genre_id: int,
        limit: int = 20,
        exclude_ids: List[int] = None
    ) -> List[Movie]:
        """Get movies by genre"""
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .join(Movie.genres)
            .where(Genre.tmdb_id == genre_id)
            .order_by(Movie.popularity.desc())
        )

        if exclude_ids:
            stmt = stmt.where(Movie.id.notin_(exclude_ids))

        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_similar_movies(
        self,
        movie_id: int,
        limit: int = 10
    ) -> List[Movie]:
        """Get similar movies based on genres and keywords"""
        movie = await self.get_movie(movie_id)
        if not movie:
            return []

        # Get genre IDs
        genre_ids = [g.tmdb_id for g in movie.genres]

        # Find movies with similar genres
        stmt = (
            select(Movie)
            .options(selectinload(Movie.genres))
            .join(Movie.genres)
            .where(
                Genre.tmdb_id.in_(genre_ids),
                Movie.id != movie_id
            )
            .group_by(Movie.id)
            .order_by(func.count(Genre.id).desc(), Movie.popularity.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_all_genres(self) -> List[Genre]:
        """Get all genres"""
        result = await self.db.execute(
            select(Genre).order_by(Genre.name)
        )
        return list(result.scalars().all())

    async def get_movies_for_onboarding(self, count: int = 20) -> List[Movie]:
        """Get diverse popular movies for onboarding"""
        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(
                Movie.vote_count >= 1000,
                Movie.vote_average >= 7.0
            )
            .order_by(Movie.popularity.desc())
            .limit(count)
        )
        return list(result.scalars().unique().all())

    async def get_movies_by_ids(self, movie_ids: List[int]) -> List[Movie]:
        """Get multiple movies by IDs"""
        if not movie_ids:
            return []

        result = await self.db.execute(
            select(Movie)
            .options(selectinload(Movie.genres))
            .where(Movie.id.in_(movie_ids))
        )
        return list(result.scalars().unique().all())

    async def get_movie_count(self) -> int:
        """Get total number of movies in database"""
        result = await self.db.execute(select(func.count(Movie.id)))
        return result.scalar() or 0
