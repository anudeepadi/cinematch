#!/usr/bin/env python3
"""
Sync all existing local interactions to Supabase.
Run from backend directory: python sync_to_supabase.py
"""

import asyncio
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.config import settings
from app.services.supabase_service import SupabaseService, supabase_service


async def get_or_create_supabase_user(local_user):
    """Get or create user in Supabase"""
    user = await supabase_service.get_or_create_user(
        email=local_user['email'],
        username=local_user['username']
    )
    return user


async def sync_interactions():
    """Sync all local interactions to Supabase"""
    import aiosqlite

    print("="*60)
    print("SYNCING LOCAL INTERACTIONS TO SUPABASE")
    print("="*60)

    # Check Supabase is configured
    if not SupabaseService.is_configured():
        print("❌ Supabase not configured!")
        return

    client = SupabaseService.get_client()
    if not client:
        print("❌ Could not get Supabase client!")
        return

    # Connect to local SQLite database
    async with aiosqlite.connect('cinematch.db') as db:
        db.row_factory = aiosqlite.Row

        # Get all users
        print("\n1. Fetching local users...")
        cursor = await db.execute("SELECT id, email, username FROM users")
        local_users = await cursor.fetchall()
        print(f"   Found {len(local_users)} local users")

        # Create mapping of local user IDs to Supabase user IDs
        user_mapping = {}
        for local_user in local_users:
            user_dict = dict(local_user)
            print(f"\n   Processing user: {user_dict['email']}")

            supabase_user = await get_or_create_supabase_user(user_dict)
            if supabase_user:
                user_mapping[user_dict['id']] = supabase_user['id']
                print(f"   ✓ Mapped local ID {user_dict['id']} -> Supabase ID {supabase_user['id'][:8]}...")
            else:
                print(f"   ✗ Failed to create Supabase user for {user_dict['email']}")

        # Get all local interactions
        print("\n2. Fetching local interactions...")
        cursor = await db.execute("""
            SELECT
                umi.id, umi.user_id, umi.movie_id, umi.interaction_type,
                umi.rating, umi.mood_at_interaction, umi.watching_with, umi.created_at,
                m.tmdb_id
            FROM user_movie_interactions umi
            JOIN movies m ON umi.movie_id = m.id
            ORDER BY umi.created_at DESC
        """)
        local_interactions = await cursor.fetchall()
        print(f"   Found {len(local_interactions)} local interactions")

        # Get existing Supabase interactions to avoid duplicates
        print("\n3. Checking existing Supabase interactions...")
        existing = client.table("user_movie_interactions").select("user_id, movie_id, interaction_type").execute()
        existing_set = set()
        for item in existing.data:
            existing_set.add((item['user_id'], item['movie_id'], item['interaction_type']))
        print(f"   Found {len(existing_set)} existing Supabase interactions")

        # Sync interactions
        print("\n4. Syncing interactions...")
        synced = 0
        skipped = 0
        failed = 0

        for interaction in local_interactions:
            interaction_dict = dict(interaction)
            local_user_id = interaction_dict['user_id']

            # Get Supabase user ID
            supabase_user_id = user_mapping.get(local_user_id)
            if not supabase_user_id:
                print(f"   ✗ No Supabase user for local user {local_user_id}")
                failed += 1
                continue

            # Check if already exists
            key = (supabase_user_id, interaction_dict['movie_id'], interaction_dict['interaction_type'])
            if key in existing_set:
                skipped += 1
                continue

            # Create in Supabase
            try:
                data = {
                    "user_id": supabase_user_id,
                    "movie_id": interaction_dict['movie_id'],
                    "tmdb_id": interaction_dict['tmdb_id'],
                    "interaction_type": interaction_dict['interaction_type'],
                    "rating": interaction_dict['rating'],
                    "context": {
                        "mood": interaction_dict['mood_at_interaction'],
                        "watching_with": interaction_dict['watching_with'],
                        "synced_from_local": True,
                        "original_created_at": interaction_dict['created_at']
                    },
                    "created_at": interaction_dict['created_at'] or datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                result = client.table("user_movie_interactions").insert(data).execute()
                if result.data:
                    synced += 1
                    existing_set.add(key)  # Add to set to avoid duplicates
                    if synced % 20 == 0:
                        print(f"   Synced {synced} interactions...")
                else:
                    failed += 1
            except Exception as e:
                print(f"   ✗ Error syncing interaction: {e}")
                failed += 1

        print(f"\n" + "="*60)
        print(f"SYNC COMPLETE")
        print(f"="*60)
        print(f"✓ Synced: {synced}")
        print(f"○ Skipped (already exists): {skipped}")
        print(f"✗ Failed: {failed}")

        # Verify final count
        final_count = client.table("user_movie_interactions").select("id", count="exact").execute()
        print(f"\nTotal interactions in Supabase: {final_count.count}")


if __name__ == "__main__":
    asyncio.run(sync_interactions())
