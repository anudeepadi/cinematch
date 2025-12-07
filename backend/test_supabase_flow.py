#!/usr/bin/env python3
"""
Test script to verify Supabase integration and user interaction flow.
Run from backend directory: python test_supabase_flow.py
"""

import asyncio
import sys
from datetime import datetime

# Add the app to path
sys.path.insert(0, '.')

from app.config import settings
from app.services.supabase_service import SupabaseService, supabase_service


def test_config():
    """Test 1: Check configuration"""
    print("\n" + "="*60)
    print("TEST 1: Configuration Check")
    print("="*60)

    print(f"SUPABASE_URL: {settings.supabase_url[:30]}..." if settings.supabase_url else "SUPABASE_URL: NOT SET")
    print(f"SUPABASE_KEY: {settings.supabase_key[:20]}..." if settings.supabase_key else "SUPABASE_KEY: NOT SET")
    print(f"SUPABASE_SECRET_KEY: {settings.supabase_secret_key[:20]}..." if settings.supabase_secret_key else "SUPABASE_SECRET_KEY: NOT SET")

    is_configured = SupabaseService.is_configured()
    print(f"\nSupabaseService.is_configured(): {is_configured}")

    return is_configured


def test_client():
    """Test 2: Check client initialization"""
    print("\n" + "="*60)
    print("TEST 2: Client Initialization")
    print("="*60)

    client = SupabaseService.get_client()
    if client:
        print("✓ Supabase client initialized successfully")
        return True
    else:
        print("✗ Failed to initialize Supabase client")
        return False


def test_tables_exist():
    """Test 3: Check if tables exist"""
    print("\n" + "="*60)
    print("TEST 3: Table Existence Check")
    print("="*60)

    client = SupabaseService.get_client()
    if not client:
        print("✗ No client available")
        return False

    tables = ["users", "user_preferences", "user_movie_interactions", "recommendation_sessions", "companion_links"]

    for table in tables:
        try:
            result = client.table(table).select("*").limit(1).execute()
            print(f"✓ Table '{table}' exists - {len(result.data)} rows sampled")
        except Exception as e:
            print(f"✗ Table '{table}' error: {e}")
            return False

    return True


async def test_user_creation():
    """Test 4: Create a test user"""
    print("\n" + "="*60)
    print("TEST 4: User Creation")
    print("="*60)

    test_email = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"

    print(f"Creating test user: {test_email}")

    user = await supabase_service.get_or_create_user(
        email=test_email,
        username=test_username
    )

    if user:
        print(f"✓ User created successfully!")
        print(f"  ID: {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Username: {user['username']}")
        return user
    else:
        print("✗ Failed to create user")
        return None


async def test_interaction_creation(user_id: str):
    """Test 5: Create a test interaction"""
    print("\n" + "="*60)
    print("TEST 5: Interaction Creation")
    print("="*60)

    print(f"Creating test interaction for user {user_id}")

    interaction = await supabase_service.create_interaction(
        user_id=user_id,
        movie_id=12345,
        tmdb_id=550,  # Fight Club TMDB ID
        interaction_type="favorite",
        context={"test": True, "source": "test_script"}
    )

    if interaction:
        print(f"✓ Interaction created successfully!")
        print(f"  ID: {interaction['id']}")
        print(f"  Movie ID: {interaction['movie_id']}")
        print(f"  Type: {interaction['interaction_type']}")
        return interaction
    else:
        print("✗ Failed to create interaction")
        return None


def test_query_interactions():
    """Test 6: Query all interactions"""
    print("\n" + "="*60)
    print("TEST 6: Query All Interactions")
    print("="*60)

    client = SupabaseService.get_client()
    if not client:
        print("✗ No client available")
        return

    try:
        result = client.table("user_movie_interactions").select("*").order("created_at", desc=True).limit(10).execute()

        if result.data:
            print(f"✓ Found {len(result.data)} interactions:")
            for i, interaction in enumerate(result.data, 1):
                print(f"\n  {i}. ID: {interaction['id'][:8]}...")
                print(f"     User: {interaction['user_id'][:8]}...")
                print(f"     Movie: {interaction['movie_id']} (TMDB: {interaction['tmdb_id']})")
                print(f"     Type: {interaction['interaction_type']}")
                print(f"     Created: {interaction['created_at']}")
        else:
            print("✗ No interactions found in database")
    except Exception as e:
        print(f"✗ Error querying interactions: {e}")


def test_query_users():
    """Test 7: Query all users"""
    print("\n" + "="*60)
    print("TEST 7: Query All Users")
    print("="*60)

    client = SupabaseService.get_client()
    if not client:
        print("✗ No client available")
        return

    try:
        result = client.table("users").select("*").order("created_at", desc=True).limit(10).execute()

        if result.data:
            print(f"✓ Found {len(result.data)} users:")
            for i, user in enumerate(result.data, 1):
                print(f"\n  {i}. ID: {user['id'][:8]}...")
                print(f"     Email: {user['email']}")
                print(f"     Username: {user['username']}")
                print(f"     Created: {user['created_at']}")
        else:
            print("✗ No users found in database")
    except Exception as e:
        print(f"✗ Error querying users: {e}")


async def main():
    print("\n" + "#"*60)
    print("# SUPABASE INTEGRATION TEST")
    print("#"*60)

    # Test 1: Configuration
    if not test_config():
        print("\n❌ FAILED: Supabase not configured. Check your .env file.")
        return

    # Test 2: Client
    if not test_client():
        print("\n❌ FAILED: Could not create Supabase client.")
        return

    # Test 3: Tables
    if not test_tables_exist():
        print("\n❌ FAILED: Some tables are missing. Run the SQL schema in Supabase.")
        return

    # Test 4: User creation
    user = await test_user_creation()
    if not user:
        print("\n❌ FAILED: Could not create test user.")
        return

    # Test 5: Interaction creation
    interaction = await test_interaction_creation(user['id'])
    if not interaction:
        print("\n❌ FAILED: Could not create test interaction.")
        return

    # Test 6: Query interactions
    test_query_interactions()

    # Test 7: Query users
    test_query_users()

    print("\n" + "#"*60)
    print("# ALL TESTS PASSED! ✓")
    print("#"*60)
    print("\nSupabase is working correctly. The issue may be in how the")
    print("backend syncs interactions. Check the [SUPABASE] logs when")
    print("you perform actions in the app.")


if __name__ == "__main__":
    asyncio.run(main())
