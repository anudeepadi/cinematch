#!/usr/bin/env python3
"""
Database seeding script for CineMatch.

This script populates the database with:
1. All movie genres from TMDB
2. Popular movies (~2000 from 100 pages)
3. Top rated movies (~500 from 25 pages)

Usage:
    python scripts/seed_database.py [--pages PAGES] [--top-rated-pages PAGES]
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.services.tmdb_service import TMDBService
from app.config import settings


def progress_callback(current_page: int, total_pages: int, movie_count: int):
    """Print progress during seeding"""
    percent = (current_page / total_pages) * 100
    print(f"\r  Progress: {current_page}/{total_pages} pages ({percent:.1f}%) - {movie_count} movies", end="", flush=True)


async def seed_database(
    popular_pages: int = 50,
    top_rated_pages: int = 25
):
    """Main seeding function"""
    if not settings.tmdb_api_key:
        print("Error: TMDB_API_KEY not set in environment or .env file")
        print("Get your API key from: https://www.themoviedb.org/settings/api")
        return

    print("=" * 60)
    print("CineMatch Database Seeder")
    print("=" * 60)

    # Initialize database
    print("\n[1/4] Initializing database...")
    await init_db()
    print("  Database initialized.")

    async with AsyncSessionLocal() as db:
        tmdb_service = TMDBService(db)

        try:
            # Sync genres
            print("\n[2/4] Syncing genres from TMDB...")
            genre_count = await tmdb_service.sync_genres()
            print(f"  Synced {genre_count} new genres.")

            # Seed popular movies
            print(f"\n[3/4] Fetching popular movies ({popular_pages} pages)...")
            popular_count = await tmdb_service.seed_popular_movies(
                pages=popular_pages,
                progress_callback=progress_callback
            )
            print(f"\n  Added {popular_count} popular movies.")

            # Seed top rated movies
            print(f"\n[4/4] Fetching top rated movies ({top_rated_pages} pages)...")
            top_count = await tmdb_service.seed_top_rated_movies(pages=top_rated_pages)
            print(f"  Added {top_count} top rated movies.")

            # Summary
            from sqlalchemy import select, func
            from app.models.movie import Movie, Genre

            movie_count = await db.execute(select(func.count(Movie.id)))
            genre_count = await db.execute(select(func.count(Genre.id)))

            print("\n" + "=" * 60)
            print("Seeding Complete!")
            print("=" * 60)
            print(f"  Total movies in database: {movie_count.scalar()}")
            print(f"  Total genres in database: {genre_count.scalar()}")

        finally:
            await tmdb_service.close()


def main():
    parser = argparse.ArgumentParser(description="Seed the CineMatch database with movie data")
    parser.add_argument(
        "--pages",
        type=int,
        default=50,
        help="Number of pages of popular movies to fetch (20 movies/page, default: 50)"
    )
    parser.add_argument(
        "--top-rated-pages",
        type=int,
        default=25,
        help="Number of pages of top rated movies to fetch (default: 25)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick seed with fewer movies (5 pages popular, 2 pages top rated)"
    )

    args = parser.parse_args()

    if args.quick:
        popular_pages = 5
        top_rated_pages = 2
    else:
        popular_pages = args.pages
        top_rated_pages = args.top_rated_pages

    asyncio.run(seed_database(popular_pages, top_rated_pages))


if __name__ == "__main__":
    main()
