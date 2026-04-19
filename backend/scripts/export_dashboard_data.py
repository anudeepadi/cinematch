#!/usr/bin/env python3
"""
Export analytics data to CSV files for Looker Studio dashboards.

This script connects to the PostgreSQL database and exports 5 CSV files
to the data/dashboard/ directory:

1. engagement_metrics.csv - Daily active users with moving averages
2. algorithm_performance.csv - Recommendation algorithm comparison
3. genre_trends.csv - Monthly genre interaction trends
4. top_movies.csv - Top movies by engagement
5. user_cohorts.csv - User retention by signup cohort

Usage:
    python scripts/export_dashboard_data.py
    python scripts/export_dashboard_data.py --output-dir /path/to/output
"""

import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings


# Default output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "dashboard"


async def get_db_session() -> AsyncSession:
    """Create and return a database session"""
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return session_maker()


async def export_engagement_metrics(db: AsyncSession, output_dir: Path):
    """Export daily engagement metrics with 7-day and 30-day moving averages"""
    print("Exporting engagement_metrics.csv...")

    query = text("""
        WITH daily_active AS (
            SELECT 
                DATE(created_at) as date,
                COUNT(DISTINCT user_id) as active_users
            FROM user_movie_interactions
            WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY DATE(created_at)
        ),
        with_averages AS (
            SELECT 
                date,
                active_users,
                ROUND(AVG(active_users) OVER (
                    ORDER BY date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                )::numeric, 2) as ma_7day,
                ROUND(AVG(active_users) OVER (
                    ORDER BY date
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                )::numeric, 2) as ma_30day
            FROM daily_active
        )
        SELECT * FROM with_averages
        ORDER BY date
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    output_file = output_dir / "engagement_metrics.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "active_users", "ma_7day", "ma_30day"])
        for row in rows:
            writer.writerow([row.date, row.active_users, row.ma_7day, row.ma_30day])

    print(f"  -> Exported {len(rows)} rows to {output_file}")


async def export_algorithm_performance(db: AsyncSession, output_dir: Path):
    """Export recommendation algorithm performance metrics"""
    print("Exporting algorithm_performance.csv...")

    query = text("""
        WITH session_recs AS (
            SELECT 
                rs.id as session_id,
                rs.user_id,
                jsonb_array_elements(rs.recommendations::jsonb) as rec
            FROM recommendation_sessions rs
            WHERE rs.recommendations IS NOT NULL
        ),
        algorithm_extracts AS (
            SELECT 
                session_id,
                user_id,
                (rec->>'movie_id')::int as movie_id,
                rec->>'source' as algorithm
            FROM session_recs
        ),
        algorithm_stats AS (
            SELECT 
                ae.algorithm,
                COUNT(DISTINCT ae.session_id) as total_recs,
                COUNT(CASE WHEN umi.interaction_type = 'watch' THEN 1 END) as watch_count,
                COUNT(CASE WHEN umi.interaction_type = 'favorite' THEN 1 END) as favorite_count,
                COUNT(umi.id) as total_interactions
            FROM algorithm_extracts ae
            LEFT JOIN user_movie_interactions umi 
                ON ae.user_id = umi.user_id AND ae.movie_id = umi.movie_id
            WHERE ae.algorithm IS NOT NULL
            GROUP BY ae.algorithm
        ),
        ranked AS (
            SELECT 
                algorithm,
                total_recs,
                ROUND(watch_count::numeric / NULLIF(total_interactions, 0) * 100, 2) as watch_rate,
                ROUND(favorite_count::numeric / NULLIF(total_interactions, 0) * 100, 2) as favorite_rate,
                RANK() OVER (
                    ORDER BY (
                        watch_count::numeric / NULLIF(total_interactions, 0) * 0.6 +
                        favorite_count::numeric / NULLIF(total_interactions, 0) * 0.4
                    ) DESC NULLS LAST
                ) as rank
            FROM algorithm_stats
            WHERE total_recs > 0
        )
        SELECT * FROM ranked ORDER BY rank
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    output_file = output_dir / "algorithm_performance.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["algorithm", "total_recs", "watch_rate", "favorite_rate", "rank"])
        for row in rows:
            writer.writerow([
                row.algorithm or "unknown",
                row.total_recs or 0,
                row.watch_rate or 0,
                row.favorite_rate or 0,
                row.rank or 0
            ])

    print(f"  -> Exported {len(rows)} rows to {output_file}")


async def export_genre_trends(db: AsyncSession, output_dir: Path):
    """Export monthly genre interaction trends"""
    print("Exporting genre_trends.csv...")

    query = text("""
        WITH genre_monthly AS (
            SELECT 
                g.name as genre,
                TO_CHAR(DATE_TRUNC('month', umi.created_at), 'YYYY-MM') as month,
                COUNT(*) as interactions
            FROM user_movie_interactions umi
            JOIN movie_genres mg ON umi.movie_id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.id
            WHERE umi.created_at >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY g.name, DATE_TRUNC('month', umi.created_at)
        ),
        with_growth AS (
            SELECT 
                genre,
                month,
                interactions,
                LAG(interactions) OVER (PARTITION BY genre ORDER BY month) as prev_interactions,
                ROUND(
                    (interactions - LAG(interactions) OVER (PARTITION BY genre ORDER BY month))::numeric 
                    / NULLIF(LAG(interactions) OVER (PARTITION BY genre ORDER BY month), 0) * 100, 
                    2
                ) as growth_pct
            FROM genre_monthly
        )
        SELECT * FROM with_growth
        ORDER BY month DESC, interactions DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    output_file = output_dir / "genre_trends.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "genre", "interactions", "growth_pct"])
        for row in rows:
            writer.writerow([row.month, row.genre, row.interactions, row.growth_pct])

    print(f"  -> Exported {len(rows)} rows to {output_file}")


async def export_top_movies(db: AsyncSession, output_dir: Path):
    """Export top movies by total engagement"""
    print("Exporting top_movies.csv...")

    query = text("""
        WITH movie_stats AS (
            SELECT 
                m.title,
                COUNT(*) as total_interactions,
                COUNT(CASE WHEN umi.interaction_type IN ('watch', 'watched') THEN 1 END) as watches,
                COUNT(CASE WHEN umi.interaction_type = 'favorite' THEN 1 END) as favorites
            FROM user_movie_interactions umi
            JOIN movies m ON umi.movie_id = m.id
            GROUP BY m.id, m.title
        ),
        ranked AS (
            SELECT 
                title,
                total_interactions,
                watches,
                favorites,
                RANK() OVER (ORDER BY total_interactions DESC) as engagement_rank
            FROM movie_stats
        )
        SELECT * FROM ranked
        WHERE engagement_rank <= 100
        ORDER BY engagement_rank
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    output_file = output_dir / "top_movies.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "total_interactions", "watches", "favorites", "engagement_rank"])
        for row in rows:
            writer.writerow([
                row.title, 
                row.total_interactions, 
                row.watches, 
                row.favorites, 
                row.engagement_rank
            ])

    print(f"  -> Exported {len(rows)} rows to {output_file}")


async def export_user_cohorts(db: AsyncSession, output_dir: Path):
    """Export user retention by signup week cohort"""
    print("Exporting user_cohorts.csv...")

    query = text("""
        WITH user_cohorts AS (
            SELECT 
                id as user_id,
                DATE_TRUNC('week', created_at) as cohort_week
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
        ),
        cohort_sizes AS (
            SELECT 
                cohort_week,
                COUNT(*) as cohort_size
            FROM user_cohorts
            GROUP BY cohort_week
        ),
        user_activity AS (
            SELECT 
                uc.user_id,
                uc.cohort_week,
                DATE_TRUNC('week', umi.created_at) as activity_week
            FROM user_cohorts uc
            LEFT JOIN user_movie_interactions umi ON uc.user_id = umi.user_id
        ),
        retention AS (
            SELECT 
                ua.cohort_week,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_week + INTERVAL '1 week' THEN ua.user_id 
                END) as week_1_users,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_week + INTERVAL '2 weeks' THEN ua.user_id 
                END) as week_2_users,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_week + INTERVAL '4 weeks' THEN ua.user_id 
                END) as week_4_users
            FROM user_activity ua
            GROUP BY ua.cohort_week
        )
        SELECT 
            TO_CHAR(cs.cohort_week, 'YYYY-MM-DD') as cohort_week,
            cs.cohort_size,
            ROUND(COALESCE(r.week_1_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_1_retention,
            ROUND(COALESCE(r.week_2_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_2_retention,
            ROUND(COALESCE(r.week_4_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_4_retention
        FROM cohort_sizes cs
        LEFT JOIN retention r ON cs.cohort_week = r.cohort_week
        WHERE cs.cohort_week <= CURRENT_DATE - INTERVAL '4 weeks'
        ORDER BY cs.cohort_week DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    output_file = output_dir / "user_cohorts.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["cohort_week", "cohort_size", "week_1_retention", "week_2_retention", "week_4_retention"])
        for row in rows:
            writer.writerow([
                row.cohort_week,
                row.cohort_size,
                row.week_1_retention or 0,
                row.week_2_retention or 0,
                row.week_4_retention or 0
            ])

    print(f"  -> Exported {len(rows)} rows to {output_file}")


async def main(output_dir: Path):
    """Main export function"""
    print(f"\n{'='*60}")
    print(f"CineMatch Analytics Data Export")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get database session
    db = await get_db_session()

    try:
        # Export all datasets
        await export_engagement_metrics(db, output_dir)
        await export_algorithm_performance(db, output_dir)
        await export_genre_trends(db, output_dir)
        await export_top_movies(db, output_dir)
        await export_user_cohorts(db, output_dir)

        print(f"\n{'='*60}")
        print(f"Export completed successfully!")
        print(f"Files written to: {output_dir}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nError during export: {e}")
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export CineMatch analytics data to CSV files for Looker Studio"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})"
    )

    args = parser.parse_args()
    asyncio.run(main(args.output_dir))
