"""
Analytics response schemas for PostgreSQL CTE/window function endpoints.
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class EngagementDataPoint(BaseModel):
    """Single day of engagement data"""
    activity_date: date
    active_users: int
    ma_7day: Optional[float] = None
    growth_rate: Optional[float] = None


class EngagementResponse(BaseModel):
    """Response for user engagement analytics"""
    time_range: str = Field(..., description="Requested time range: 7d, 30d, 90d, or all")
    total_days: int = Field(..., description="Number of days in the response")
    data: List[EngagementDataPoint] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "time_range": "30d",
                "total_days": 30,
                "data": [
                    {
                        "activity_date": "2024-01-15",
                        "active_users": 150,
                        "ma_7day": 142.5,
                        "growth_rate": 5.2
                    }
                ]
            }
        }


class AlgorithmPerformance(BaseModel):
    """Performance metrics for a single recommendation algorithm"""
    algorithm: str = Field(..., description="Algorithm name (e.g., collaborative, content_based, claude)")
    total_sessions: int = Field(..., description="Total recommendation sessions using this algorithm")
    watch_rate: float = Field(..., description="Percentage of recommendations that led to 'watch' action")
    favorite_rate: float = Field(..., description="Percentage of recommendations that led to 'favorite' action")
    rank: int = Field(..., description="Rank by overall performance")

    class Config:
        json_schema_extra = {
            "example": {
                "algorithm": "collaborative",
                "total_sessions": 1250,
                "watch_rate": 35.5,
                "favorite_rate": 12.3,
                "rank": 1
            }
        }


class AlgorithmPerformanceResponse(BaseModel):
    """Response for algorithm comparison analytics"""
    total_algorithms: int
    data: List[AlgorithmPerformance] = Field(default_factory=list)


class GenreTrend(BaseModel):
    """Genre trend data for a single period"""
    genre: str = Field(..., description="Genre name")
    period: str = Field(..., description="Period identifier (e.g., '2024-W03' or '2024-01')")
    count: int = Field(..., description="Number of interactions in this period")
    prev_count: Optional[int] = Field(None, description="Count from previous period")
    growth_pct: Optional[float] = Field(None, description="Growth percentage from previous period")

    class Config:
        json_schema_extra = {
            "example": {
                "genre": "Action",
                "period": "2024-01",
                "count": 450,
                "prev_count": 380,
                "growth_pct": 18.4
            }
        }


class GenreTrendsResponse(BaseModel):
    """Response for genre trends analytics"""
    period_type: str = Field(..., description="Period type: weekly or monthly")
    total_periods: int
    data: List[GenreTrend] = Field(default_factory=list)


class CohortRetention(BaseModel):
    """Retention data for a user cohort"""
    cohort_date: date = Field(..., description="Week/month the cohort signed up")
    cohort_size: int = Field(..., description="Number of users in this cohort")
    week_1_retention: float = Field(..., description="Percentage retained after 1 week")
    week_2_retention: float = Field(..., description="Percentage retained after 2 weeks")
    week_4_retention: float = Field(..., description="Percentage retained after 4 weeks")

    class Config:
        json_schema_extra = {
            "example": {
                "cohort_date": "2024-01-01",
                "cohort_size": 50,
                "week_1_retention": 72.0,
                "week_2_retention": 58.0,
                "week_4_retention": 45.0
            }
        }


class CohortRetentionResponse(BaseModel):
    """Response for user retention analytics"""
    total_cohorts: int
    data: List[CohortRetention] = Field(default_factory=list)


class MovieMomentum(BaseModel):
    """Movie momentum/trending data"""
    movie_id: int
    title: str
    momentum_score: float = Field(..., description="Weighted trending score")
    rank: int = Field(..., description="Rank by momentum score")
    trend_direction: str = Field(..., description="Trend direction: rising, stable, or falling")
    recent_interactions: int = Field(..., description="Interactions in the window period")
    previous_interactions: int = Field(..., description="Interactions in the previous window")

    class Config:
        json_schema_extra = {
            "example": {
                "movie_id": 123,
                "title": "Inception",
                "momentum_score": 85.5,
                "rank": 1,
                "trend_direction": "rising",
                "recent_interactions": 45,
                "previous_interactions": 28
            }
        }


class MovieMomentumResponse(BaseModel):
    """Response for movie momentum/trending analytics"""
    window_days: int = Field(..., description="Window size in days for momentum calculation")
    limit: int = Field(..., description="Number of movies returned")
    data: List[MovieMomentum] = Field(default_factory=list)


# Summary/Dashboard schemas
class AnalyticsSummary(BaseModel):
    """High-level analytics summary"""
    total_users: int
    total_movies: int
    total_interactions: int
    total_sessions: int
    avg_daily_active_users: float
    top_genre: Optional[str] = None
    top_algorithm: Optional[str] = None


class DashboardResponse(BaseModel):
    """Combined dashboard response"""
    summary: AnalyticsSummary
    recent_engagement: EngagementResponse
    top_algorithms: AlgorithmPerformanceResponse
    trending_movies: MovieMomentumResponse
