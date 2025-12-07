#!/usr/bin/env python3
"""
Migrate all data from local SQLite to Supabase PostgreSQL.

Usage:
    1. Set SUPABASE_DB_URL in your .env file (get from Supabase Dashboard → Settings → Database → Connection string)
    2. Run: python scripts/migrate_to_supabase.py
"""

import asyncio
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from datetime import datetime

from app.config import settings
from app.database import Base
from app.models import User, Movie, Genre, UserMovieInteraction, WatchHistory, UserPreference


def parse_datetime(value):
    """Convert SQLite datetime string to Python datetime or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Try common formats
        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_bool(value):
    """Convert SQLite integer (0/1) to Python boolean."""
    if value is None:
        return False
    return bool(value)


def get_sqlite_connection():
    """Connect to local SQLite database."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cinematch.db")
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found at {db_path}")
        sys.exit(1)
    return sqlite3.connect(db_path)


def get_supabase_url():
    """Get and validate Supabase PostgreSQL URL."""
    url = settings.supabase_db_url
    if not url:
        print("❌ SUPABASE_DB_URL not set in .env")
        print("   Get it from: Supabase Dashboard → Settings → Database → Connection string (URI)")
        print("   It looks like: postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres")
        sys.exit(1)

    # Convert to async driver
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


async def drop_existing_tables(engine):
    """Drop existing tables that might conflict."""
    print("🗑️  Dropping existing tables (if any)...")
    async with engine.begin() as conn:
        # Drop tables in reverse dependency order
        tables_to_drop = [
            'recommendation_feedback',
            'recommendation_sessions',
            'companion_links',
            'watch_history',
            'user_movie_interactions',
            'user_preferences',
            'movie_genres',
            'movies',
            'genres',
            'users'
        ]
        for table in tables_to_drop:
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
            except Exception as e:
                print(f"   Warning dropping {table}: {e}")
    print("✅ Existing tables dropped")


async def create_tables(engine):
    """Create all tables in Supabase PostgreSQL."""
    print("📦 Creating tables in Supabase...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")


def read_sqlite_data(conn):
    """Read all data from SQLite."""
    cursor = conn.cursor()
    data = {}

    # Read genres
    cursor.execute("SELECT id, tmdb_id, name FROM genres")
    data['genres'] = cursor.fetchall()
    print(f"   📖 Read {len(data['genres'])} genres")

    # Read movies (note: "cast" is a reserved keyword, so we quote it)
    cursor.execute("""
        SELECT id, tmdb_id, imdb_id, title, original_title, tagline, overview,
               release_date, release_year, runtime, vote_average, vote_count, popularity,
               poster_path, backdrop_path, original_language, spoken_languages,
               production_countries, "cast", directors, keywords, mood_scores,
               content_embedding, is_adult, status, created_at, updated_at
        FROM movies
    """)
    data['movies'] = cursor.fetchall()
    print(f"   📖 Read {len(data['movies'])} movies")

    # Read movie_genres associations
    cursor.execute("SELECT movie_id, genre_id FROM movie_genres")
    data['movie_genres'] = cursor.fetchall()
    print(f"   📖 Read {len(data['movie_genres'])} movie-genre associations")

    # Read users
    cursor.execute("""
        SELECT id, email, username, hashed_password, full_name, avatar_url,
               preferred_genres, year_range_min, year_range_max, preferred_languages,
               mood_action, mood_comedy, mood_drama, mood_horror, mood_romance,
               mood_scifi, mood_thriller, mood_documentary, watch_alone_preference,
               is_active, is_verified, is_onboarded, created_at, updated_at, last_login
        FROM users
    """)
    data['users'] = cursor.fetchall()
    print(f"   📖 Read {len(data['users'])} users")

    # Read user_movie_interactions
    cursor.execute("""
        SELECT id, user_id, movie_id, interaction_type, rating,
               mood_at_interaction, watching_with, context_notes, created_at
        FROM user_movie_interactions
    """)
    data['interactions'] = cursor.fetchall()
    print(f"   📖 Read {len(data['interactions'])} interactions")

    # Read user_preferences
    cursor.execute("""
        SELECT id, user_id, genre_weights, preferred_decades, new_releases_interest,
               classics_interest, actor_preferences, director_preferences,
               keyword_preferences, avg_rating, total_watched, total_passed,
               favorite_count, preference_embedding, updated_at
        FROM user_preferences
    """)
    data['preferences'] = cursor.fetchall()
    print(f"   📖 Read {len(data['preferences'])} user preferences")

    return data


async def insert_data(session: AsyncSession, data: dict):
    """Insert all data into Supabase PostgreSQL."""

    # Insert genres
    if data['genres']:
        print("   📝 Inserting genres...")
        for row in data['genres']:
            await session.execute(
                text("""
                    INSERT INTO genres (id, tmdb_id, name)
                    VALUES (:id, :tmdb_id, :name)
                    ON CONFLICT (id) DO UPDATE SET tmdb_id = :tmdb_id, name = :name
                """),
                {"id": row[0], "tmdb_id": row[1], "name": row[2]}
            )
        await session.commit()
        print(f"   ✅ Inserted {len(data['genres'])} genres")

    # Insert movies
    if data['movies']:
        print("   📝 Inserting movies...")
        batch_size = 100
        for i in range(0, len(data['movies']), batch_size):
            batch = data['movies'][i:i+batch_size]
            for row in batch:
                await session.execute(
                    text("""
                        INSERT INTO movies (
                            id, tmdb_id, imdb_id, title, original_title, tagline, overview,
                            release_date, release_year, runtime, vote_average, vote_count, popularity,
                            poster_path, backdrop_path, original_language, spoken_languages,
                            production_countries, "cast", directors, keywords, mood_scores,
                            content_embedding, is_adult, status, created_at, updated_at
                        ) VALUES (
                            :id, :tmdb_id, :imdb_id, :title, :original_title, :tagline, :overview,
                            :release_date, :release_year, :runtime, :vote_average, :vote_count, :popularity,
                            :poster_path, :backdrop_path, :original_language, :spoken_languages,
                            :production_countries, :cast, :directors, :keywords, :mood_scores,
                            :content_embedding, :is_adult, :status, :created_at, :updated_at
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            title = :title, overview = :overview, vote_average = :vote_average
                    """),
                    {
                        "id": row[0], "tmdb_id": row[1], "imdb_id": row[2], "title": row[3],
                        "original_title": row[4], "tagline": row[5], "overview": row[6],
                        "release_date": parse_datetime(row[7]), "release_year": row[8], "runtime": row[9],
                        "vote_average": row[10], "vote_count": row[11], "popularity": row[12],
                        "poster_path": row[13], "backdrop_path": row[14], "original_language": row[15],
                        "spoken_languages": row[16], "production_countries": row[17],
                        "cast": row[18], "directors": row[19], "keywords": row[20],
                        "mood_scores": row[21], "content_embedding": row[22], "is_adult": row[23],
                        "status": row[24], "created_at": parse_datetime(row[25]), "updated_at": parse_datetime(row[26])
                    }
                )
            await session.commit()
            print(f"      Inserted {min(i+batch_size, len(data['movies']))}/{len(data['movies'])} movies")
        print(f"   ✅ Inserted {len(data['movies'])} movies")

    # Insert movie_genres
    if data['movie_genres']:
        print("   📝 Inserting movie-genre associations...")
        for row in data['movie_genres']:
            await session.execute(
                text("""
                    INSERT INTO movie_genres (movie_id, genre_id)
                    VALUES (:movie_id, :genre_id)
                    ON CONFLICT DO NOTHING
                """),
                {"movie_id": row[0], "genre_id": row[1]}
            )
        await session.commit()
        print(f"   ✅ Inserted {len(data['movie_genres'])} associations")

    # Insert users
    if data['users']:
        print("   📝 Inserting users...")
        for row in data['users']:
            await session.execute(
                text("""
                    INSERT INTO users (
                        id, email, username, hashed_password, full_name, avatar_url,
                        preferred_genres, year_range_min, year_range_max, preferred_languages,
                        mood_action, mood_comedy, mood_drama, mood_horror, mood_romance,
                        mood_scifi, mood_thriller, mood_documentary, watch_alone_preference,
                        is_active, is_verified, is_onboarded, created_at, updated_at, last_login
                    ) VALUES (
                        :id, :email, :username, :hashed_password, :full_name, :avatar_url,
                        :preferred_genres, :year_range_min, :year_range_max, :preferred_languages,
                        :mood_action, :mood_comedy, :mood_drama, :mood_horror, :mood_romance,
                        :mood_scifi, :mood_thriller, :mood_documentary, :watch_alone_preference,
                        :is_active, :is_verified, :is_onboarded, :created_at, :updated_at, :last_login
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        email = :email, username = :username, is_onboarded = :is_onboarded
                """),
                {
                    "id": row[0], "email": row[1], "username": row[2], "hashed_password": row[3],
                    "full_name": row[4], "avatar_url": row[5], "preferred_genres": row[6],
                    "year_range_min": row[7], "year_range_max": row[8], "preferred_languages": row[9],
                    "mood_action": row[10], "mood_comedy": row[11], "mood_drama": row[12],
                    "mood_horror": row[13], "mood_romance": row[14], "mood_scifi": row[15],
                    "mood_thriller": row[16], "mood_documentary": row[17], "watch_alone_preference": row[18],
                    "is_active": parse_bool(row[19]), "is_verified": parse_bool(row[20]), "is_onboarded": parse_bool(row[21]),
                    "created_at": parse_datetime(row[22]), "updated_at": parse_datetime(row[23]), "last_login": parse_datetime(row[24])
                }
            )
        await session.commit()
        print(f"   ✅ Inserted {len(data['users'])} users")

    # Insert interactions
    if data['interactions']:
        print("   📝 Inserting interactions...")
        for row in data['interactions']:
            await session.execute(
                text("""
                    INSERT INTO user_movie_interactions (
                        id, user_id, movie_id, interaction_type, rating,
                        mood_at_interaction, watching_with, context_notes, created_at
                    ) VALUES (
                        :id, :user_id, :movie_id, :interaction_type, :rating,
                        :mood_at_interaction, :watching_with, :context_notes, :created_at
                    )
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": row[0], "user_id": row[1], "movie_id": row[2],
                    "interaction_type": row[3], "rating": row[4],
                    "mood_at_interaction": row[5], "watching_with": row[6],
                    "context_notes": row[7], "created_at": parse_datetime(row[8])
                }
            )
        await session.commit()
        print(f"   ✅ Inserted {len(data['interactions'])} interactions")

    # Insert preferences
    if data['preferences']:
        print("   📝 Inserting user preferences...")
        for row in data['preferences']:
            await session.execute(
                text("""
                    INSERT INTO user_preferences (
                        id, user_id, genre_weights, preferred_decades, new_releases_interest,
                        classics_interest, actor_preferences, director_preferences,
                        keyword_preferences, avg_rating, total_watched, total_passed,
                        favorite_count, preference_embedding, updated_at
                    ) VALUES (
                        :id, :user_id, :genre_weights, :preferred_decades, :new_releases_interest,
                        :classics_interest, :actor_preferences, :director_preferences,
                        :keyword_preferences, :avg_rating, :total_watched, :total_passed,
                        :favorite_count, :preference_embedding, :updated_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        genre_weights = :genre_weights, total_watched = :total_watched
                """),
                {
                    "id": row[0], "user_id": row[1], "genre_weights": row[2],
                    "preferred_decades": row[3], "new_releases_interest": row[4],
                    "classics_interest": row[5], "actor_preferences": row[6],
                    "director_preferences": row[7], "keyword_preferences": row[8],
                    "avg_rating": row[9], "total_watched": row[10], "total_passed": row[11],
                    "favorite_count": row[12], "preference_embedding": row[13], "updated_at": parse_datetime(row[14])
                }
            )
        await session.commit()
        print(f"   ✅ Inserted {len(data['preferences'])} user preferences")

    # Reset sequences to max ID
    print("   🔧 Resetting sequences...")
    tables = ['genres', 'movies', 'users', 'user_movie_interactions', 'user_preferences']
    for table in tables:
        await session.execute(text(f"""
            SELECT setval(pg_get_serial_sequence('{table}', 'id'),
                   COALESCE((SELECT MAX(id) FROM {table}), 1))
        """))
    await session.commit()
    print("   ✅ Sequences reset")


async def verify_migration(session: AsyncSession):
    """Verify migration was successful."""
    print("\n📊 Verifying migration...")

    tables = [
        ('genres', 'SELECT COUNT(*) FROM genres'),
        ('movies', 'SELECT COUNT(*) FROM movies'),
        ('users', 'SELECT COUNT(*) FROM users'),
        ('user_movie_interactions', 'SELECT COUNT(*) FROM user_movie_interactions'),
        ('user_preferences', 'SELECT COUNT(*) FROM user_preferences'),
    ]

    for table_name, query in tables:
        result = await session.execute(text(query))
        count = result.scalar()
        print(f"   {table_name}: {count} rows")


async def main():
    print("🚀 Starting migration from SQLite to Supabase PostgreSQL\n")

    # Get Supabase URL
    supabase_url = get_supabase_url()
    print(f"🔗 Connecting to Supabase PostgreSQL...")

    # Create async engine for Supabase
    engine = create_async_engine(supabase_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Read SQLite data
    print("\n📖 Reading data from local SQLite...")
    sqlite_conn = get_sqlite_connection()
    data = read_sqlite_data(sqlite_conn)
    sqlite_conn.close()

    # Drop existing tables and create fresh ones
    print()
    await drop_existing_tables(engine)
    await create_tables(engine)

    # Insert data
    print("\n📝 Inserting data into Supabase...")
    async with AsyncSessionLocal() as session:
        await insert_data(session, data)
        await verify_migration(session)

    await engine.dispose()

    print("\n✅ Migration completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Set SUPABASE_DB_URL in Railway environment variables")
    print("   2. Deploy to Railway")
    print("   3. Your app will now use Supabase PostgreSQL directly!")


if __name__ == "__main__":
    asyncio.run(main())
