#!/usr/bin/env python3
"""
PySpark User Analytics Pipeline for CineMatch.

This pipeline processes user interaction data at scale using Apache Spark.
It contains 4 main jobs:

1. User Engagement Analysis - Daily engagement with lag, cumulative metrics
2. Genre Trends Analysis - Genre popularity with ranking and moving averages
3. Algorithm Comparison - Monthly algorithm performance aggregation
4. User Segmentation - RFM-based user segmentation using NTILE

Output: Parquet files for each analysis

Usage:
    spark-submit spark_jobs/user_analytics.py --output-dir output/
    spark-submit spark_jobs/user_analytics.py --database-url postgresql://... --output-dir output/

Requirements:
    - PySpark 3.5.0+
    - PostgreSQL JDBC driver
"""

import argparse
import os
from datetime import datetime, timedelta
from typing import Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField, IntegerType, StringType, 
    FloatType, TimestampType, DateType
)


def get_spark_session(app_name: str = "CineMatch-Analytics") -> SparkSession:
    """Create and return a Spark session"""
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .getOrCreate()
    )


def load_data_from_postgres(
    spark: SparkSession, 
    database_url: str, 
    table: str
) -> DataFrame:
    """Load data from PostgreSQL table"""
    # Parse database URL to JDBC format
    # Expected format: postgresql://user:pass@host:port/dbname
    if database_url.startswith("postgresql://"):
        jdbc_url = database_url.replace("postgresql://", "jdbc:postgresql://")
    else:
        jdbc_url = database_url

    # Extract user/password if in URL
    import re
    match = re.match(r"jdbc:postgresql://([^:]+):([^@]+)@(.+)", jdbc_url)
    if match:
        user, password, host_db = match.groups()
        jdbc_url = f"jdbc:postgresql://{host_db}"
        properties = {"user": user, "password": password, "driver": "org.postgresql.Driver"}
    else:
        properties = {"driver": "org.postgresql.Driver"}

    return spark.read.jdbc(jdbc_url, table, properties=properties)


def load_sample_data(spark: SparkSession) -> tuple:
    """Load sample data for testing without database connection"""
    # Sample interactions
    interactions_schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("user_id", IntegerType(), False),
        StructField("movie_id", IntegerType(), False),
        StructField("interaction_type", StringType(), False),
        StructField("created_at", TimestampType(), False),
    ])
    
    # Generate sample data
    from datetime import datetime, timedelta
    import random
    
    base_date = datetime.now()
    sample_interactions = []
    
    for i in range(1000):
        sample_interactions.append((
            i + 1,
            random.randint(1, 100),  # user_id
            random.randint(1, 500),  # movie_id
            random.choice(["watch", "favorite", "pass", "watched"]),
            base_date - timedelta(days=random.randint(0, 90))
        ))
    
    interactions_df = spark.createDataFrame(sample_interactions, interactions_schema)
    
    # Sample users
    users_schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("created_at", TimestampType(), False),
    ])
    
    users_data = [
        (i, base_date - timedelta(days=random.randint(30, 180)))
        for i in range(1, 101)
    ]
    users_df = spark.createDataFrame(users_data, users_schema)
    
    # Sample movies with genres
    movies_schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("title", StringType(), False),
    ])
    
    movies_data = [(i, f"Movie {i}") for i in range(1, 501)]
    movies_df = spark.createDataFrame(movies_data, movies_schema)
    
    # Movie genres
    genres = ["Action", "Comedy", "Drama", "Horror", "Romance", "Sci-Fi", "Thriller"]
    movie_genres_schema = StructType([
        StructField("movie_id", IntegerType(), False),
        StructField("genre_name", StringType(), False),
    ])
    
    movie_genres_data = []
    for movie_id in range(1, 501):
        for genre in random.sample(genres, random.randint(1, 3)):
            movie_genres_data.append((movie_id, genre))
    
    movie_genres_df = spark.createDataFrame(movie_genres_data, movie_genres_schema)
    
    # Recommendation sessions (simplified)
    sessions_schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("user_id", IntegerType(), False),
        StructField("algorithm", StringType(), False),
        StructField("created_at", TimestampType(), False),
    ])
    
    algorithms = ["collaborative", "content_based", "claude", "openai", "gemini", "random_forest", "knn"]
    sessions_data = [
        (i, random.randint(1, 100), random.choice(algorithms), base_date - timedelta(days=random.randint(0, 90)))
        for i in range(1, 501)
    ]
    sessions_df = spark.createDataFrame(sessions_data, sessions_schema)
    
    return interactions_df, users_df, movies_df, movie_genres_df, sessions_df


# =============================================================================
# JOB 1: User Engagement Analysis
# =============================================================================
def run_user_engagement_analysis(
    interactions_df: DataFrame,
    output_dir: str
) -> None:
    """
    Analyze user engagement patterns using window functions.
    
    Window Functions Used:
    - LAG: Compare to previous day's activity
    - ROW_NUMBER: Rank user activity days
    - Cumulative SUM: Running total of interactions
    
    Output:
    - user_daily_engagement.parquet: Daily engagement per user
    - user_summary.parquet: User-level summary statistics
    """
    print("\n" + "="*60)
    print("JOB 1: User Engagement Analysis")
    print("="*60)

    # Daily user engagement
    daily_engagement = (
        interactions_df
        .withColumn("activity_date", F.to_date("created_at"))
        .groupBy("user_id", "activity_date")
        .agg(
            F.count("*").alias("daily_interactions"),
            F.sum(F.when(F.col("interaction_type") == "watch", 1).otherwise(0)).alias("watches"),
            F.sum(F.when(F.col("interaction_type") == "favorite", 1).otherwise(0)).alias("favorites"),
            F.sum(F.when(F.col("interaction_type") == "pass", 1).otherwise(0)).alias("passes")
        )
    )

    # Window for per-user analysis
    user_window = Window.partitionBy("user_id").orderBy("activity_date")

    # Add window function calculations
    daily_with_windows = (
        daily_engagement
        .withColumn(
            "prev_day_interactions", 
            F.lag("daily_interactions", 1).over(user_window)
        )
        .withColumn(
            "interaction_growth",
            F.when(
                F.col("prev_day_interactions") > 0,
                (F.col("daily_interactions") - F.col("prev_day_interactions")) 
                / F.col("prev_day_interactions") * 100
            ).otherwise(F.lit(None))
        )
        .withColumn(
            "cumulative_interactions",
            F.sum("daily_interactions").over(user_window.rowsBetween(Window.unboundedPreceding, Window.currentRow))
        )
        .withColumn(
            "activity_day_rank",
            F.row_number().over(user_window)
        )
    )

    # Save daily engagement
    daily_output = f"{output_dir}/user_daily_engagement.parquet"
    daily_with_windows.write.mode("overwrite").parquet(daily_output)
    print(f"  -> Saved user_daily_engagement.parquet ({daily_with_windows.count()} rows)")

    # User summary statistics
    user_summary = (
        daily_with_windows
        .groupBy("user_id")
        .agg(
            F.count("activity_date").alias("active_days"),
            F.sum("daily_interactions").alias("total_interactions"),
            F.sum("watches").alias("total_watches"),
            F.sum("favorites").alias("total_favorites"),
            F.avg("daily_interactions").alias("avg_daily_interactions"),
            F.min("activity_date").alias("first_activity"),
            F.max("activity_date").alias("last_activity")
        )
        .withColumn(
            "engagement_score",
            F.col("total_watches") * 2 + F.col("total_favorites") * 3
        )
    )

    # Save user summary
    summary_output = f"{output_dir}/user_summary.parquet"
    user_summary.write.mode("overwrite").parquet(summary_output)
    print(f"  -> Saved user_summary.parquet ({user_summary.count()} rows)")


# =============================================================================
# JOB 2: Genre Trends Analysis
# =============================================================================
def run_genre_trends_analysis(
    interactions_df: DataFrame,
    movie_genres_df: DataFrame,
    output_dir: str
) -> None:
    """
    Analyze genre popularity trends over time.
    
    Window Functions Used:
    - RANK: Rank genres by popularity within each month
    - 3-month moving average for trend smoothing
    
    Output:
    - genre_trends.parquet: Monthly genre trends with ranking
    """
    print("\n" + "="*60)
    print("JOB 2: Genre Trends Analysis")
    print("="*60)

    # Join interactions with movie genres
    interactions_with_genres = (
        interactions_df
        .join(movie_genres_df, interactions_df.movie_id == movie_genres_df.movie_id, "inner")
        .drop(movie_genres_df.movie_id)
    )

    # Monthly genre aggregation
    monthly_genres = (
        interactions_with_genres
        .withColumn("month", F.date_trunc("month", "created_at"))
        .groupBy("month", "genre_name")
        .agg(
            F.count("*").alias("interaction_count"),
            F.countDistinct("user_id").alias("unique_users"),
            F.sum(F.when(F.col("interaction_type") == "watch", 1).otherwise(0)).alias("watch_count"),
            F.sum(F.when(F.col("interaction_type") == "favorite", 1).otherwise(0)).alias("favorite_count")
        )
    )

    # Window for ranking and moving average
    genre_window = Window.partitionBy("genre_name").orderBy("month")
    month_window = Window.partitionBy("month").orderBy(F.desc("interaction_count"))

    # Add analytics
    genre_trends = (
        monthly_genres
        .withColumn(
            "monthly_rank",
            F.rank().over(month_window)
        )
        .withColumn(
            "ma_3month",
            F.avg("interaction_count").over(
                genre_window.rowsBetween(-2, 0)
            )
        )
        .withColumn(
            "prev_month_count",
            F.lag("interaction_count", 1).over(genre_window)
        )
        .withColumn(
            "month_over_month_growth",
            F.when(
                F.col("prev_month_count") > 0,
                (F.col("interaction_count") - F.col("prev_month_count"))
                / F.col("prev_month_count") * 100
            ).otherwise(F.lit(None))
        )
    )

    # Save results
    output_path = f"{output_dir}/genre_trends.parquet"
    genre_trends.write.mode("overwrite").parquet(output_path)
    print(f"  -> Saved genre_trends.parquet ({genre_trends.count()} rows)")


# =============================================================================
# JOB 3: Algorithm Comparison
# =============================================================================
def run_algorithm_comparison(
    sessions_df: DataFrame,
    interactions_df: DataFrame,
    output_dir: str
) -> None:
    """
    Compare recommendation algorithm performance monthly.
    
    Output:
    - algorithm_performance.parquet: Monthly algorithm metrics
    """
    print("\n" + "="*60)
    print("JOB 3: Algorithm Comparison")
    print("="*60)

    # Monthly algorithm performance
    monthly_performance = (
        sessions_df
        .withColumn("month", F.date_trunc("month", "created_at"))
        .groupBy("month", "algorithm")
        .agg(
            F.count("*").alias("session_count"),
            F.countDistinct("user_id").alias("unique_users")
        )
    )

    # Join with outcomes
    session_outcomes = (
        sessions_df
        .join(
            interactions_df.select("user_id", "interaction_type"),
            "user_id",
            "left"
        )
        .groupBy("algorithm")
        .agg(
            F.count("*").alias("total_recommendations"),
            F.sum(F.when(F.col("interaction_type") == "watch", 1).otherwise(0)).alias("watches"),
            F.sum(F.when(F.col("interaction_type") == "favorite", 1).otherwise(0)).alias("favorites")
        )
        .withColumn(
            "watch_rate",
            F.col("watches") / F.col("total_recommendations") * 100
        )
        .withColumn(
            "favorite_rate",
            F.col("favorites") / F.col("total_recommendations") * 100
        )
        .withColumn(
            "combined_score",
            F.col("watch_rate") * 0.6 + F.col("favorite_rate") * 0.4
        )
    )

    # Rank algorithms
    rank_window = Window.orderBy(F.desc("combined_score"))
    algorithm_performance = session_outcomes.withColumn(
        "performance_rank",
        F.rank().over(rank_window)
    )

    # Save results
    output_path = f"{output_dir}/algorithm_performance.parquet"
    algorithm_performance.write.mode("overwrite").parquet(output_path)
    print(f"  -> Saved algorithm_performance.parquet ({algorithm_performance.count()} rows)")


# =============================================================================
# JOB 4: User Segmentation (RFM)
# =============================================================================
def run_user_segmentation(
    interactions_df: DataFrame,
    users_df: DataFrame,
    output_dir: str
) -> None:
    """
    Segment users using RFM (Recency, Frequency, Monetary) analysis.
    
    Window Functions Used:
    - NTILE(5): Divide users into 5 quintiles for each RFM dimension
    
    Segments:
    - Champions (score >= 12)
    - Loyal Customers (score >= 9, high frequency)
    - Recent Customers (score >= 9, high recency)
    - Promising (score >= 6)
    - At Risk (low recency)
    - Need Attention (score <= 4)
    
    Output:
    - user_segments.parquet: User-level RFM scores and segments
    - segment_summary.parquet: Segment-level aggregations
    """
    print("\n" + "="*60)
    print("JOB 4: User Segmentation (RFM)")
    print("="*60)

    # Calculate RFM metrics per user
    current_date = F.current_date()

    rfm_metrics = (
        interactions_df
        .groupBy("user_id")
        .agg(
            F.datediff(current_date, F.max(F.to_date("created_at"))).alias("recency_days"),
            F.count("*").alias("frequency"),
            # Monetary = weighted interaction value
            F.sum(
                F.when(F.col("interaction_type") == "favorite", 3)
                .when(F.col("interaction_type") == "watch", 2)
                .when(F.col("interaction_type") == "watched", 1)
                .otherwise(0)
            ).alias("monetary")
        )
    )

    # Create quintiles using NTILE
    rfm_with_scores = (
        rfm_metrics
        .withColumn(
            "recency_score",
            F.ntile(5).over(Window.orderBy("recency_days"))  # Lower recency = higher score
        )
        .withColumn(
            "frequency_score",
            F.ntile(5).over(Window.orderBy(F.desc("frequency")))
        )
        .withColumn(
            "monetary_score",
            F.ntile(5).over(Window.orderBy(F.desc("monetary")))
        )
        # Invert recency score (lower days = higher score)
        .withColumn("recency_score", F.lit(6) - F.col("recency_score"))
        .withColumn(
            "rfm_score",
            F.col("recency_score") + F.col("frequency_score") + F.col("monetary_score")
        )
    )

    # Assign segments
    user_segments = (
        rfm_with_scores
        .withColumn(
            "segment",
            F.when(F.col("rfm_score") >= 12, "Champions")
            .when(
                (F.col("rfm_score") >= 9) & (F.col("frequency_score") >= 4),
                "Loyal Customers"
            )
            .when(
                (F.col("rfm_score") >= 9) & (F.col("recency_score") >= 4),
                "Recent Customers"
            )
            .when(F.col("rfm_score") >= 6, "Promising")
            .when(F.col("recency_score") <= 2, "At Risk")
            .otherwise("Need Attention")
        )
    )

    # Save user segments
    segments_output = f"{output_dir}/user_segments.parquet"
    user_segments.write.mode("overwrite").parquet(segments_output)
    print(f"  -> Saved user_segments.parquet ({user_segments.count()} rows)")

    # Segment summary
    segment_summary = (
        user_segments
        .groupBy("segment")
        .agg(
            F.count("user_id").alias("user_count"),
            F.avg("recency_days").alias("avg_recency"),
            F.avg("frequency").alias("avg_frequency"),
            F.avg("monetary").alias("avg_monetary"),
            F.avg("rfm_score").alias("avg_rfm_score")
        )
        .orderBy(F.desc("avg_rfm_score"))
    )

    # Save segment summary
    summary_output = f"{output_dir}/segment_summary.parquet"
    segment_summary.write.mode("overwrite").parquet(summary_output)
    print(f"  -> Saved segment_summary.parquet ({segment_summary.count()} rows)")


# =============================================================================
# Main Pipeline
# =============================================================================
def main(output_dir: str, database_url: Optional[str] = None):
    """Run the complete analytics pipeline"""
    print("\n" + "="*60)
    print("CineMatch PySpark Analytics Pipeline")
    print("="*60)
    print(f"Output Directory: {output_dir}")
    print(f"Database URL: {'Provided' if database_url else 'Using sample data'}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)

    # Initialize Spark
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # Load data
        if database_url:
            print("\nLoading data from PostgreSQL...")
            interactions_df = load_data_from_postgres(spark, database_url, "user_movie_interactions")
            users_df = load_data_from_postgres(spark, database_url, "users")
            movies_df = load_data_from_postgres(spark, database_url, "movies")
            # For genres, we need to join
            movie_genres_df = load_data_from_postgres(spark, database_url, "movie_genres")
            genres_df = load_data_from_postgres(spark, database_url, "genres")
            movie_genres_df = movie_genres_df.join(
                genres_df.select("id", F.col("name").alias("genre_name")),
                movie_genres_df.genre_id == genres_df.id,
                "inner"
            ).select("movie_id", "genre_name")
            sessions_df = load_data_from_postgres(spark, database_url, "recommendation_sessions")
            # Extract algorithm from JSON
            sessions_df = sessions_df.withColumn(
                "algorithm",
                F.get_json_object(F.col("recommendations"), "$[0].source")
            )
        else:
            print("\nUsing sample data for demonstration...")
            interactions_df, users_df, movies_df, movie_genres_df, sessions_df = load_sample_data(spark)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Run all jobs
        run_user_engagement_analysis(interactions_df, output_dir)
        run_genre_trends_analysis(interactions_df, movie_genres_df, output_dir)
        run_algorithm_comparison(sessions_df, interactions_df, output_dir)
        run_user_segmentation(interactions_df, users_df, output_dir)

        print("\n" + "="*60)
        print("Pipeline completed successfully!")
        print(f"Output files written to: {output_dir}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CineMatch PySpark Analytics Pipeline"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for parquet files (default: output/)"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL database URL (optional, uses sample data if not provided)"
    )

    args = parser.parse_args()
    main(args.output_dir, args.database_url)
