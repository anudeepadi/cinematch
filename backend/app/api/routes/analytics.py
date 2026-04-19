"""
Analytics API endpoints using PostgreSQL CTEs and window functions.

All endpoints are public (no authentication required).
"""

from datetime import date, timedelta
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.schemas.analytics import (
    EngagementResponse,
    EngagementDataPoint,
    AlgorithmPerformanceResponse,
    AlgorithmPerformance,
    GenreTrendsResponse,
    GenreTrend,
    CohortRetentionResponse,
    CohortRetention,
    MovieMomentumResponse,
    MovieMomentum,
)

router = APIRouter()


@router.get("/engagement", response_model=EngagementResponse)
async def get_engagement_metrics(
    time_range: Literal["7d", "30d", "90d", "all"] = Query(
        "30d", description="Time range for engagement data"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get daily user engagement metrics with 7-day moving average and growth rates.
    
    Uses PostgreSQL CTEs and window functions:
    - AVG() OVER for 7-day moving average
    - LAG() for day-over-day growth calculation
    """
    # Calculate days from time_range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "all": 3650}
    days = days_map.get(time_range, 30)

    query = text("""
        WITH daily_active AS (
            SELECT 
                DATE(created_at) as activity_date,
                COUNT(DISTINCT user_id) as active_users
            FROM user_movie_interactions
            WHERE created_at >= CURRENT_DATE - INTERVAL :days DAY
            GROUP BY DATE(created_at)
        ),
        with_moving_avg AS (
            SELECT 
                activity_date,
                active_users,
                AVG(active_users) OVER (
                    ORDER BY activity_date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as ma_7day,
                LAG(active_users, 1) OVER (ORDER BY activity_date) as prev_day
            FROM daily_active
        )
        SELECT 
            activity_date,
            active_users,
            ROUND(ma_7day::numeric, 2) as ma_7day,
            CASE 
                WHEN prev_day > 0 
                THEN ROUND((active_users - prev_day)::numeric / NULLIF(prev_day, 0) * 100, 2)
                ELSE NULL 
            END as growth_rate
        FROM with_moving_avg
        ORDER BY activity_date
    """)

    result = await db.execute(query, {"days": days})
    rows = result.fetchall()

    data = [
        EngagementDataPoint(
            activity_date=row.activity_date,
            active_users=row.active_users,
            ma_7day=float(row.ma_7day) if row.ma_7day else None,
            growth_rate=float(row.growth_rate) if row.growth_rate else None,
        )
        for row in rows
    ]

    return EngagementResponse(
        time_range=time_range,
        total_days=len(data),
        data=data,
    )


@router.get("/algorithm-performance", response_model=AlgorithmPerformanceResponse)
async def get_algorithm_performance(
    db: AsyncSession = Depends(get_db),
):
    """
    Compare recommendation algorithm performance.
    
    Uses PostgreSQL CTEs and RANK() window function to rank algorithms
    by watch and favorite conversion rates.
    """
    query = text("""
        WITH session_recommendations AS (
            -- Extract algorithm sources from JSON recommendations
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
            FROM session_recommendations
        ),
        algorithm_outcomes AS (
            SELECT 
                ae.algorithm,
                COUNT(DISTINCT ae.session_id) as total_sessions,
                COUNT(CASE WHEN umi.interaction_type = 'watch' THEN 1 END) as watch_count,
                COUNT(CASE WHEN umi.interaction_type = 'favorite' THEN 1 END) as favorite_count,
                COUNT(umi.id) as total_interactions
            FROM algorithm_extracts ae
            LEFT JOIN user_movie_interactions umi 
                ON ae.user_id = umi.user_id 
                AND ae.movie_id = umi.movie_id
            WHERE ae.algorithm IS NOT NULL
            GROUP BY ae.algorithm
        ),
        ranked AS (
            SELECT 
                algorithm,
                total_sessions,
                ROUND(watch_count::numeric / NULLIF(total_interactions, 0) * 100, 2) as watch_rate,
                ROUND(favorite_count::numeric / NULLIF(total_interactions, 0) * 100, 2) as favorite_rate,
                RANK() OVER (
                    ORDER BY (
                        watch_count::numeric / NULLIF(total_interactions, 0) * 0.6 +
                        favorite_count::numeric / NULLIF(total_interactions, 0) * 0.4
                    ) DESC NULLS LAST
                ) as rank
            FROM algorithm_outcomes
            WHERE total_sessions > 0
        )
        SELECT * FROM ranked
        ORDER BY rank
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    data = [
        AlgorithmPerformance(
            algorithm=row.algorithm or "unknown",
            total_sessions=row.total_sessions or 0,
            watch_rate=float(row.watch_rate) if row.watch_rate else 0.0,
            favorite_rate=float(row.favorite_rate) if row.favorite_rate else 0.0,
            rank=row.rank or 0,
        )
        for row in rows
    ]

    return AlgorithmPerformanceResponse(
        total_algorithms=len(data),
        data=data,
    )


@router.get("/genre-trends", response_model=GenreTrendsResponse)
async def get_genre_trends(
    period_type: Literal["weekly", "monthly"] = Query(
        "monthly", description="Aggregation period: weekly or monthly"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze genre popularity trends over time.
    
    Uses PostgreSQL CTEs and LAG() window function for period-over-period growth.
    """
    # Use different date truncation based on period type
    if period_type == "weekly":
        trunc_format = "week"
        interval = "1 week"
    else:
        trunc_format = "month"
        interval = "1 month"

    query = text(f"""
        WITH genre_interactions AS (
            SELECT 
                g.name as genre,
                DATE_TRUNC(:trunc_format, umi.created_at) as period_start,
                COUNT(*) as interaction_count
            FROM user_movie_interactions umi
            JOIN movie_genres mg ON umi.movie_id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.id
            WHERE umi.created_at >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY g.name, DATE_TRUNC(:trunc_format, umi.created_at)
        ),
        with_prev AS (
            SELECT 
                genre,
                TO_CHAR(period_start, 
                    CASE WHEN :trunc_format = 'week' THEN 'YYYY-"W"IW' ELSE 'YYYY-MM' END
                ) as period,
                interaction_count as count,
                LAG(interaction_count) OVER (
                    PARTITION BY genre 
                    ORDER BY period_start
                ) as prev_count
            FROM genre_interactions
        )
        SELECT 
            genre,
            period,
            count,
            prev_count,
            CASE 
                WHEN prev_count > 0 
                THEN ROUND((count - prev_count)::numeric / NULLIF(prev_count, 0) * 100, 2)
                ELSE NULL 
            END as growth_pct
        FROM with_prev
        ORDER BY period DESC, count DESC
    """)

    result = await db.execute(query, {"trunc_format": trunc_format})
    rows = result.fetchall()

    data = [
        GenreTrend(
            genre=row.genre,
            period=row.period,
            count=row.count or 0,
            prev_count=row.prev_count,
            growth_pct=float(row.growth_pct) if row.growth_pct else None,
        )
        for row in rows
    ]

    # Count unique periods
    unique_periods = len(set(r.period for r in data))

    return GenreTrendsResponse(
        period_type=period_type,
        total_periods=unique_periods,
        data=data,
    )


@router.get("/user-retention", response_model=CohortRetentionResponse)
async def get_user_retention(
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate user retention by signup cohort.
    
    Uses PostgreSQL DATE_TRUNC for cohort grouping and window functions
    for retention rate calculation across 1, 2, and 4 week windows.
    """
    query = text("""
        WITH user_cohorts AS (
            -- Group users by their signup week
            SELECT 
                id as user_id,
                DATE_TRUNC('week', created_at) as cohort_date
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '3 months'
        ),
        cohort_sizes AS (
            SELECT 
                cohort_date,
                COUNT(*) as cohort_size
            FROM user_cohorts
            GROUP BY cohort_date
        ),
        user_activity AS (
            -- Get each user's activity weeks
            SELECT 
                uc.user_id,
                uc.cohort_date,
                DATE_TRUNC('week', umi.created_at) as activity_week
            FROM user_cohorts uc
            LEFT JOIN user_movie_interactions umi ON uc.user_id = umi.user_id
        ),
        retention_weeks AS (
            SELECT 
                ua.cohort_date,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_date + INTERVAL '1 week' THEN ua.user_id 
                END) as week_1_users,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_date + INTERVAL '2 weeks' THEN ua.user_id 
                END) as week_2_users,
                COUNT(DISTINCT CASE 
                    WHEN activity_week = cohort_date + INTERVAL '4 weeks' THEN ua.user_id 
                END) as week_4_users
            FROM user_activity ua
            GROUP BY ua.cohort_date
        )
        SELECT 
            cs.cohort_date::date,
            cs.cohort_size,
            ROUND(COALESCE(rw.week_1_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_1_retention,
            ROUND(COALESCE(rw.week_2_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_2_retention,
            ROUND(COALESCE(rw.week_4_users, 0)::numeric / NULLIF(cs.cohort_size, 0) * 100, 2) as week_4_retention
        FROM cohort_sizes cs
        LEFT JOIN retention_weeks rw ON cs.cohort_date = rw.cohort_date
        WHERE cs.cohort_date <= CURRENT_DATE - INTERVAL '4 weeks'
        ORDER BY cs.cohort_date DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    data = [
        CohortRetention(
            cohort_date=row.cohort_date,
            cohort_size=row.cohort_size or 0,
            week_1_retention=float(row.week_1_retention) if row.week_1_retention else 0.0,
            week_2_retention=float(row.week_2_retention) if row.week_2_retention else 0.0,
            week_4_retention=float(row.week_4_retention) if row.week_4_retention else 0.0,
        )
        for row in rows
    ]

    return CohortRetentionResponse(
        total_cohorts=len(data),
        data=data,
    )


@router.get("/movie-momentum", response_model=MovieMomentumResponse)
async def get_movie_momentum(
    window_days: int = Query(7, ge=1, le=90, description="Window size in days"),
    limit: int = Query(20, ge=1, le=100, description="Number of movies to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate movie momentum/trending scores.
    
    Uses PostgreSQL RANK() window function with weighted scoring:
    - Recent interactions (window period) weighted higher
    - Compares to previous window for trend direction
    """
    query = text("""
        WITH recent_interactions AS (
            -- Count interactions in current window
            SELECT 
                movie_id,
                COUNT(*) as recent_count,
                SUM(CASE 
                    WHEN interaction_type = 'favorite' THEN 3
                    WHEN interaction_type = 'watch' THEN 2
                    WHEN interaction_type = 'watched' THEN 1
                    ELSE 0
                END) as weighted_recent
            FROM user_movie_interactions
            WHERE created_at >= CURRENT_DATE - INTERVAL :window_days DAY
            GROUP BY movie_id
        ),
        previous_interactions AS (
            -- Count interactions in previous window
            SELECT 
                movie_id,
                COUNT(*) as prev_count,
                SUM(CASE 
                    WHEN interaction_type = 'favorite' THEN 3
                    WHEN interaction_type = 'watch' THEN 2
                    WHEN interaction_type = 'watched' THEN 1
                    ELSE 0
                END) as weighted_prev
            FROM user_movie_interactions
            WHERE created_at >= CURRENT_DATE - INTERVAL :double_window DAY
              AND created_at < CURRENT_DATE - INTERVAL :window_days DAY
            GROUP BY movie_id
        ),
        momentum_calc AS (
            SELECT 
                m.id as movie_id,
                m.title,
                COALESCE(ri.recent_count, 0) as recent_interactions,
                COALESCE(pi.prev_count, 0) as previous_interactions,
                -- Momentum score: recent weighted * 0.7 + growth factor * 0.3
                ROUND((
                    COALESCE(ri.weighted_recent, 0) * 0.7 +
                    CASE 
                        WHEN COALESCE(pi.weighted_prev, 0) > 0 
                        THEN (COALESCE(ri.weighted_recent, 0) - COALESCE(pi.weighted_prev, 0))::numeric 
                             / pi.weighted_prev * 30
                        ELSE COALESCE(ri.weighted_recent, 0) * 0.3
                    END
                )::numeric, 2) as momentum_score,
                CASE 
                    WHEN COALESCE(ri.weighted_recent, 0) > COALESCE(pi.weighted_prev, 0) * 1.2 THEN 'rising'
                    WHEN COALESCE(ri.weighted_recent, 0) < COALESCE(pi.weighted_prev, 0) * 0.8 THEN 'falling'
                    ELSE 'stable'
                END as trend_direction
            FROM movies m
            LEFT JOIN recent_interactions ri ON m.id = ri.movie_id
            LEFT JOIN previous_interactions pi ON m.id = pi.movie_id
            WHERE COALESCE(ri.recent_count, 0) > 0 OR COALESCE(pi.prev_count, 0) > 0
        ),
        ranked AS (
            SELECT 
                movie_id,
                title,
                momentum_score,
                recent_interactions,
                previous_interactions,
                trend_direction,
                RANK() OVER (ORDER BY momentum_score DESC) as rank
            FROM momentum_calc
        )
        SELECT * FROM ranked
        WHERE rank <= :limit
        ORDER BY rank
    """)

    result = await db.execute(
        query, 
        {
            "window_days": window_days,
            "double_window": window_days * 2,
            "limit": limit
        }
    )
    rows = result.fetchall()

    data = [
        MovieMomentum(
            movie_id=row.movie_id,
            title=row.title,
            momentum_score=float(row.momentum_score) if row.momentum_score else 0.0,
            rank=row.rank,
            trend_direction=row.trend_direction or "stable",
            recent_interactions=row.recent_interactions or 0,
            previous_interactions=row.previous_interactions or 0,
        )
        for row in rows
    ]

    return MovieMomentumResponse(
        window_days=window_days,
        limit=limit,
        data=data,
    )
