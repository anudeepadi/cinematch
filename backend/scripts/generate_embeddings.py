#!/usr/bin/env python3
"""
Generate embeddings for all movies in the database.

Usage:
    python scripts/generate_embeddings.py [--force]
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.tasks.embedding_generator import generate_all_embeddings


async def main(force_regenerate: bool = False):
    print("=" * 60)
    print("CineMatch Embedding Generator")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        await generate_all_embeddings(db, force_regenerate=force_regenerate)

    print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate movie embeddings")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regenerate all embeddings, even for movies that already have them"
    )

    args = parser.parse_args()
    asyncio.run(main(force_regenerate=args.force))
