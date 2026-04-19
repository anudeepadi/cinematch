-- ============================================================================
-- CINEMATCH MOVIE RECOMMENDATION ANALYTICS QUERIES
-- PostgreSQL Production-Ready Analytics Suite
-- ============================================================================
--
-- This file contains advanced SQL analytics queries demonstrating:
-- - Common Table Expressions (CTEs) for complex aggregations
-- - Window Functions: LAG, LEAD, ROW_NUMBER, RANK, DENSE_RANK, NTILE
-- - Window Frames: ROWS BETWEEN, RANGE BETWEEN
-- - Moving averages and trend analysis
-- - User engagement, algorithm performance, and business insights
--
-- Database Schema Reference:
-- - users: User accounts with preferences
-- - movies: Movie catalog from TMDB
-- - genres / movie_genres: Genre classification
-- - user_movie_interactions: watch/pass/favorite/rating events
-- - watch_history: Detailed viewing records
-- - recommendation_sessions: Algorithm-generated sessions
-- - recommendation_feedback: User responses to recommendations
-- ============================================================================


-- ============================================================================
-- SECTION 1: USER ENGAGEMENT METRICS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Daily Active Users with 7-Day Moving Average
-- ----------------------------------------------------------------------------
-- Business Value: Track user engagement trends, identify growth/decline patterns
-- Technique: CTE + AVG() OVER with window frame
--
-- Output Schema:
--   activity_date DATE       - Calendar date
--   daily_active_users INT   - Unique users with interactions that day
--   dau_7day_avg NUMERIC     - Rolling 7-day average DAU
--   dau_change_pct NUMERIC   - Day-over-day percentage change
-- ----------------------------------------------------------------------------

WITH daily_activity AS (
    -- Aggregate daily unique active users from interactions
    SELECT
        DATE(created_at) AS activity_date,
        COUNT(DISTINCT user_id) AS daily_active_users
    FROM user_movie_interactions
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY DATE(created_at)
),
dau_with_moving_avg AS (
    -- Calculate 7-day moving average using window frame
    SELECT
        activity_date,
        daily_active_users,
        -- 7-day moving average: current day + 6 preceding days
        ROUND(
            AVG(daily_active_users) OVER (
                ORDER BY activity_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2
        ) AS dau_7day_avg,
        -- Previous day's DAU for change calculation
        LAG(daily_active_users, 1) OVER (ORDER BY activity_date) AS prev_day_dau
    FROM daily_activity
)
SELECT
    activity_date,
    daily_active_users,
    dau_7day_avg,
    -- Day-over-day percentage change
    CASE
        WHEN prev_day_dau > 0
        THEN ROUND(((daily_active_users - prev_day_dau)::NUMERIC / prev_day_dau) * 100, 2)
        ELSE NULL
    END AS dau_change_pct
FROM dau_with_moving_avg
ORDER BY activity_date DESC;

-- Suggested Index:
-- CREATE INDEX idx_interactions_created_at ON user_movie_interactions(created_at);


-- ----------------------------------------------------------------------------
-- QUERY 2: User Retention Cohort Analysis
-- ----------------------------------------------------------------------------
-- Business Value: Understand user retention by signup cohort
-- Technique: Multiple CTEs, DATE_TRUNC for cohort grouping, conditional aggregation
--
-- Output Schema:
--   cohort_month DATE        - Month of user signup
--   cohort_size INT          - Users who signed up that month
--   month_0 to month_6 INT   - Users retained in each subsequent month
--   retention_rate_m6 PCTG   - 6-month retention rate
-- ----------------------------------------------------------------------------

WITH user_cohorts AS (
    -- Assign each user to their signup cohort (month)
    SELECT
        id AS user_id,
        DATE_TRUNC('month', created_at) AS cohort_month
    FROM users
    WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
),
user_activity_months AS (
    -- Get the activity month for each user interaction
    SELECT DISTINCT
        user_id,
        DATE_TRUNC('month', created_at) AS activity_month
    FROM user_movie_interactions
    WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
),
cohort_retention AS (
    -- Join cohorts with activity to calculate months since signup
    SELECT
        uc.cohort_month,
        uc.user_id,
        uam.activity_month,
        -- Calculate months since signup
        EXTRACT(YEAR FROM AGE(uam.activity_month, uc.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(uam.activity_month, uc.cohort_month)) AS months_since_signup
    FROM user_cohorts uc
    LEFT JOIN user_activity_months uam ON uc.user_id = uam.user_id
)
SELECT
    cohort_month,
    COUNT(DISTINCT user_id) AS cohort_size,
    -- Month 0: Signup month (should be 100%)
    COUNT(DISTINCT CASE WHEN months_since_signup = 0 THEN user_id END) AS month_0,
    -- Subsequent months
    COUNT(DISTINCT CASE WHEN months_since_signup = 1 THEN user_id END) AS month_1,
    COUNT(DISTINCT CASE WHEN months_since_signup = 2 THEN user_id END) AS month_2,
    COUNT(DISTINCT CASE WHEN months_since_signup = 3 THEN user_id END) AS month_3,
    COUNT(DISTINCT CASE WHEN months_since_signup = 6 THEN user_id END) AS month_6,
    -- 6-month retention rate
    ROUND(
        COUNT(DISTINCT CASE WHEN months_since_signup = 6 THEN user_id END)::NUMERIC /
        NULLIF(COUNT(DISTINCT user_id), 0) * 100, 2
    ) AS retention_rate_m6
FROM cohort_retention
GROUP BY cohort_month
ORDER BY cohort_month DESC;


-- ----------------------------------------------------------------------------
-- QUERY 3: User Engagement Ranking with Percentiles (NTILE)
-- ----------------------------------------------------------------------------
-- Business Value: Segment users into engagement tiers for targeted campaigns
-- Technique: NTILE for percentile buckets, multiple window functions
--
-- Output Schema:
--   user_id INT              - User identifier
--   total_interactions INT   - Total interaction count
--   engagement_quartile INT  - 1 (top 25%) to 4 (bottom 25%)
--   interaction_rank INT     - Global engagement rank
--   engagement_tier VARCHAR  - Human-readable tier label
-- ----------------------------------------------------------------------------

WITH user_engagement AS (
    SELECT
        u.id AS user_id,
        u.username,
        u.created_at AS signup_date,
        COUNT(umi.id) AS total_interactions,
        COUNT(CASE WHEN umi.interaction_type = 'watch' THEN 1 END) AS watch_count,
        COUNT(CASE WHEN umi.interaction_type = 'favorite' THEN 1 END) AS favorite_count,
        COUNT(CASE WHEN umi.interaction_type = 'rating' THEN 1 END) AS rating_count,
        AVG(umi.rating) FILTER (WHERE umi.rating IS NOT NULL) AS avg_rating
    FROM users u
    LEFT JOIN user_movie_interactions umi ON u.id = umi.user_id
    WHERE u.is_active = true
    GROUP BY u.id, u.username, u.created_at
)
SELECT
    user_id,
    username,
    total_interactions,
    watch_count,
    favorite_count,
    avg_rating,
    -- Quartile assignment: 1 = top 25%, 4 = bottom 25%
    NTILE(4) OVER (ORDER BY total_interactions DESC) AS engagement_quartile,
    -- Dense rank to handle ties
    DENSE_RANK() OVER (ORDER BY total_interactions DESC) AS interaction_rank,
    -- Row number for unique ranking
    ROW_NUMBER() OVER (ORDER BY total_interactions DESC, signup_date ASC) AS unique_rank,
    -- Human-readable engagement tier
    CASE
        WHEN NTILE(4) OVER (ORDER BY total_interactions DESC) = 1 THEN 'Power User'
        WHEN NTILE(4) OVER (ORDER BY total_interactions DESC) = 2 THEN 'Active'
        WHEN NTILE(4) OVER (ORDER BY total_interactions DESC) = 3 THEN 'Casual'
        ELSE 'At-Risk'
    END AS engagement_tier
FROM user_engagement
ORDER BY total_interactions DESC
LIMIT 100;


-- ----------------------------------------------------------------------------
-- QUERY 4: User Activity Gap Analysis (Churn Detection)
-- ----------------------------------------------------------------------------
-- Business Value: Identify users at risk of churning based on activity gaps
-- Technique: LAG/LEAD for gap analysis, CASE for risk classification
--
-- Output Schema:
--   user_id INT              - User identifier
--   last_activity DATE       - Most recent activity date
--   days_since_activity INT  - Days since last interaction
--   previous_gap_days INT    - Gap before last activity
--   activity_trend VARCHAR   - Accelerating/Decelerating/Stable
--   churn_risk VARCHAR       - High/Medium/Low risk level
-- ----------------------------------------------------------------------------

WITH user_activity_timeline AS (
    SELECT
        user_id,
        DATE(created_at) AS activity_date,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS activity_rank
    FROM user_movie_interactions
),
recent_activity AS (
    SELECT
        user_id,
        activity_date AS last_activity,
        LEAD(activity_date, 1) OVER (PARTITION BY user_id ORDER BY activity_date DESC) AS prev_activity,
        LEAD(activity_date, 2) OVER (PARTITION BY user_id ORDER BY activity_date DESC) AS prev_prev_activity
    FROM user_activity_timeline
    WHERE activity_rank <= 3
),
gap_analysis AS (
    SELECT DISTINCT ON (user_id)
        user_id,
        last_activity,
        CURRENT_DATE - last_activity AS days_since_activity,
        last_activity - prev_activity AS recent_gap_days,
        prev_activity - prev_prev_activity AS previous_gap_days
    FROM recent_activity
    WHERE last_activity IS NOT NULL
    ORDER BY user_id, last_activity DESC
)
SELECT
    ga.user_id,
    u.username,
    u.email,
    ga.last_activity,
    ga.days_since_activity,
    ga.recent_gap_days,
    ga.previous_gap_days,
    -- Activity trend analysis
    CASE
        WHEN ga.recent_gap_days > ga.previous_gap_days THEN 'Decelerating'
        WHEN ga.recent_gap_days < ga.previous_gap_days THEN 'Accelerating'
        ELSE 'Stable'
    END AS activity_trend,
    -- Churn risk classification
    CASE
        WHEN ga.days_since_activity > 30 THEN 'High'
        WHEN ga.days_since_activity > 14 THEN 'Medium'
        WHEN ga.days_since_activity > 7 AND ga.recent_gap_days > ga.previous_gap_days THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk
FROM gap_analysis ga
JOIN users u ON ga.user_id = u.id
WHERE u.is_active = true
ORDER BY ga.days_since_activity DESC, ga.user_id;

-- Suggested Index:
-- CREATE INDEX idx_interactions_user_created ON user_movie_interactions(user_id, created_at DESC);


-- ============================================================================
-- SECTION 2: RECOMMENDATION ALGORITHM PERFORMANCE
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 5: Algorithm Success Rate Comparison
-- ----------------------------------------------------------------------------
-- Business Value: Compare effectiveness of different recommendation algorithms
-- Technique: CTE with JSON unnesting, PARTITION BY for algorithm grouping
--
-- Output Schema:
--   algorithm_name VARCHAR    - Claude/OpenAI/Gemini/Collaborative/Content
--   total_recommendations INT - Total recommendations generated
--   watch_actions INT         - Positive user responses
--   pass_actions INT          - Negative user responses
--   conversion_rate PCTG      - Watch / Total shown
--   avg_score NUMERIC         - Average recommendation score
-- ----------------------------------------------------------------------------

WITH recommendation_details AS (
    -- Unnest the contributing models from feedback
    SELECT
        rf.id AS feedback_id,
        rf.session_id,
        rf.user_id,
        rf.movie_id,
        rf.action,
        rf.final_score,
        rs.created_at AS session_date,
        -- Extract contributing models (stored as JSON array)
        jsonb_array_elements_text(rf.contributing_models::jsonb) AS algorithm_name
    FROM recommendation_feedback rf
    JOIN recommendation_sessions rs ON rf.session_id = rs.id
    WHERE rf.created_at >= CURRENT_DATE - INTERVAL '30 days'
),
algorithm_performance AS (
    SELECT
        algorithm_name,
        COUNT(*) AS total_recommendations,
        COUNT(CASE WHEN action = 'watch' THEN 1 END) AS watch_actions,
        COUNT(CASE WHEN action = 'pass' THEN 1 END) AS pass_actions,
        COUNT(CASE WHEN action = 'skip' THEN 1 END) AS skip_actions,
        AVG(final_score) AS avg_score
    FROM recommendation_details
    GROUP BY algorithm_name
)
SELECT
    algorithm_name,
    total_recommendations,
    watch_actions,
    pass_actions,
    skip_actions,
    -- Conversion rate: watches / (watches + passes)
    ROUND(
        watch_actions::NUMERIC / NULLIF(watch_actions + pass_actions, 0) * 100, 2
    ) AS conversion_rate,
    ROUND(avg_score::NUMERIC, 3) AS avg_score,
    -- Rank algorithms by conversion rate
    RANK() OVER (ORDER BY
        watch_actions::NUMERIC / NULLIF(watch_actions + pass_actions, 0) DESC
    ) AS performance_rank
FROM algorithm_performance
WHERE total_recommendations >= 10  -- Minimum sample size
ORDER BY conversion_rate DESC;


-- ----------------------------------------------------------------------------
-- QUERY 6: Recommendation Funnel Analysis
-- ----------------------------------------------------------------------------
-- Business Value: Track user journey from recommendation to watch to favorite
-- Technique: Multi-stage CTE, window functions for funnel progression
--
-- Output Schema:
--   week_start DATE           - Week beginning
--   recommendations_shown INT - Total recommendations displayed
--   watch_intent INT          - Users clicking "watch"
--   actually_watched INT      - Users who completed viewing
--   favorites INT             - Users who favorited
--   conversion_rate_1 PCTG    - Show → Watch intent
--   conversion_rate_2 PCTG    - Watch intent → Watched
--   conversion_rate_3 PCTG    - Watched → Favorite
-- ----------------------------------------------------------------------------

WITH weekly_recommendations AS (
    SELECT
        DATE_TRUNC('week', rs.created_at)::DATE AS week_start,
        rs.user_id,
        rs.id AS session_id,
        rs.recommendations_shown
    FROM recommendation_sessions rs
    WHERE rs.created_at >= CURRENT_DATE - INTERVAL '12 weeks'
),
weekly_watch_intent AS (
    -- Users who clicked "watch" on a recommendation
    SELECT
        DATE_TRUNC('week', created_at)::DATE AS week_start,
        user_id,
        movie_id
    FROM user_movie_interactions
    WHERE interaction_type = 'watch'
      AND created_at >= CURRENT_DATE - INTERVAL '12 weeks'
),
weekly_watched AS (
    -- Users who actually watched (from watch_history)
    SELECT
        DATE_TRUNC('week', watched_at)::DATE AS week_start,
        user_id,
        movie_id
    FROM watch_history
    WHERE watched_at >= CURRENT_DATE - INTERVAL '12 weeks'
      AND completed = true
),
weekly_favorites AS (
    SELECT
        DATE_TRUNC('week', created_at)::DATE AS week_start,
        user_id,
        movie_id
    FROM user_movie_interactions
    WHERE interaction_type = 'favorite'
      AND created_at >= CURRENT_DATE - INTERVAL '12 weeks'
),
funnel_metrics AS (
    SELECT
        wr.week_start,
        SUM(wr.recommendations_shown) AS recommendations_shown,
        COUNT(DISTINCT wwi.user_id || '-' || wwi.movie_id) AS watch_intent,
        COUNT(DISTINCT ww.user_id || '-' || ww.movie_id) AS actually_watched,
        COUNT(DISTINCT wf.user_id || '-' || wf.movie_id) AS favorites
    FROM weekly_recommendations wr
    LEFT JOIN weekly_watch_intent wwi ON wr.week_start = wwi.week_start
    LEFT JOIN weekly_watched ww ON wr.week_start = ww.week_start
    LEFT JOIN weekly_favorites wf ON wr.week_start = wf.week_start
    GROUP BY wr.week_start
)
SELECT
    week_start,
    recommendations_shown,
    watch_intent,
    actually_watched,
    favorites,
    -- Funnel conversion rates
    ROUND(watch_intent::NUMERIC / NULLIF(recommendations_shown, 0) * 100, 2) AS show_to_intent_pct,
    ROUND(actually_watched::NUMERIC / NULLIF(watch_intent, 0) * 100, 2) AS intent_to_watch_pct,
    ROUND(favorites::NUMERIC / NULLIF(actually_watched, 0) * 100, 2) AS watch_to_favorite_pct,
    -- Week-over-week change in watch intent
    LAG(watch_intent, 1) OVER (ORDER BY week_start) AS prev_week_intent,
    ROUND(
        (watch_intent - LAG(watch_intent, 1) OVER (ORDER BY week_start))::NUMERIC /
        NULLIF(LAG(watch_intent, 1) OVER (ORDER BY week_start), 0) * 100, 2
    ) AS wow_change_pct
FROM funnel_metrics
ORDER BY week_start DESC;


-- ----------------------------------------------------------------------------
-- QUERY 7: Top Performing Genres with Ranking
-- ----------------------------------------------------------------------------
-- Business Value: Identify which genres have highest user engagement
-- Technique: RANK() OVER with PARTITION BY, aggregate metrics
--
-- Output Schema:
--   genre_name VARCHAR        - Genre name
--   total_interactions INT    - Total interactions for genre
--   watch_count INT           - Watch interactions
--   avg_rating NUMERIC        - Average rating when rated
--   genre_rank INT            - Overall popularity rank
--   watch_to_interaction_ratio - Engagement depth
-- ----------------------------------------------------------------------------

WITH genre_interactions AS (
    SELECT
        g.id AS genre_id,
        g.name AS genre_name,
        umi.interaction_type,
        umi.rating,
        umi.user_id,
        umi.movie_id
    FROM user_movie_interactions umi
    JOIN movie_genres mg ON umi.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.id
    WHERE umi.created_at >= CURRENT_DATE - INTERVAL '90 days'
),
genre_metrics AS (
    SELECT
        genre_name,
        COUNT(*) AS total_interactions,
        COUNT(CASE WHEN interaction_type = 'watch' THEN 1 END) AS watch_count,
        COUNT(CASE WHEN interaction_type = 'favorite' THEN 1 END) AS favorite_count,
        COUNT(CASE WHEN interaction_type = 'pass' THEN 1 END) AS pass_count,
        AVG(rating) FILTER (WHERE rating IS NOT NULL) AS avg_rating,
        COUNT(DISTINCT user_id) AS unique_users
    FROM genre_interactions
    GROUP BY genre_name
)
SELECT
    genre_name,
    total_interactions,
    watch_count,
    favorite_count,
    pass_count,
    ROUND(avg_rating::NUMERIC, 2) AS avg_rating,
    unique_users,
    -- Watch to total interaction ratio (engagement depth)
    ROUND(watch_count::NUMERIC / NULLIF(total_interactions, 0) * 100, 2) AS engagement_depth_pct,
    -- Overall popularity rank
    RANK() OVER (ORDER BY total_interactions DESC) AS popularity_rank,
    -- Engagement quality rank (watch + favorite ratio)
    RANK() OVER (
        ORDER BY (watch_count + favorite_count)::NUMERIC / NULLIF(total_interactions, 0) DESC
    ) AS quality_rank,
    -- Rating rank (among genres with ratings)
    DENSE_RANK() OVER (ORDER BY avg_rating DESC NULLS LAST) AS rating_rank
FROM genre_metrics
ORDER BY total_interactions DESC;


-- ============================================================================
-- SECTION 3: MOVIE POPULARITY TRENDS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 8: Trending Movies with Momentum Score
-- ----------------------------------------------------------------------------
-- Business Value: Identify currently trending content for featuring
-- Technique: Window functions for trend calculation, composite scoring
--
-- Output Schema:
--   movie_id INT              - Movie identifier
--   title VARCHAR             - Movie title
--   recent_interactions INT   - Interactions in last 7 days
--   prev_week_interactions INT - Interactions 8-14 days ago
--   momentum_score NUMERIC    - Week-over-week growth rate
--   trending_rank INT         - Position in trending list
-- ----------------------------------------------------------------------------

WITH weekly_movie_activity AS (
    SELECT
        m.id AS movie_id,
        m.title,
        m.release_year,
        m.vote_average,
        m.popularity AS tmdb_popularity,
        -- Current week interactions (last 7 days)
        COUNT(CASE
            WHEN umi.created_at >= CURRENT_DATE - INTERVAL '7 days'
            THEN 1
        END) AS recent_interactions,
        -- Previous week interactions (8-14 days ago)
        COUNT(CASE
            WHEN umi.created_at >= CURRENT_DATE - INTERVAL '14 days'
             AND umi.created_at < CURRENT_DATE - INTERVAL '7 days'
            THEN 1
        END) AS prev_week_interactions,
        -- Watch vs Pass ratio
        COUNT(CASE
            WHEN umi.interaction_type = 'watch'
             AND umi.created_at >= CURRENT_DATE - INTERVAL '7 days'
            THEN 1
        END) AS recent_watches,
        COUNT(CASE
            WHEN umi.interaction_type = 'pass'
             AND umi.created_at >= CURRENT_DATE - INTERVAL '7 days'
            THEN 1
        END) AS recent_passes
    FROM movies m
    LEFT JOIN user_movie_interactions umi ON m.id = umi.movie_id
    WHERE umi.created_at >= CURRENT_DATE - INTERVAL '14 days'
    GROUP BY m.id, m.title, m.release_year, m.vote_average, m.popularity
)
SELECT
    movie_id,
    title,
    release_year,
    vote_average,
    recent_interactions,
    prev_week_interactions,
    recent_watches,
    recent_passes,
    -- Momentum score: week-over-week growth
    CASE
        WHEN prev_week_interactions > 0
        THEN ROUND(
            (recent_interactions - prev_week_interactions)::NUMERIC / prev_week_interactions * 100, 2
        )
        WHEN recent_interactions > 0 THEN 999.99  -- New trending (infinite growth)
        ELSE 0
    END AS momentum_score,
    -- Sentiment score: watches vs passes
    ROUND(
        recent_watches::NUMERIC / NULLIF(recent_watches + recent_passes, 0) * 100, 2
    ) AS positive_sentiment_pct,
    -- Trending rank based on recent activity
    RANK() OVER (ORDER BY recent_interactions DESC) AS trending_rank,
    -- Momentum rank
    RANK() OVER (
        ORDER BY
            CASE
                WHEN prev_week_interactions > 0
                THEN (recent_interactions - prev_week_interactions)::NUMERIC / prev_week_interactions
                WHEN recent_interactions > 0 THEN 999
                ELSE 0
            END DESC
    ) AS momentum_rank
FROM weekly_movie_activity
WHERE recent_interactions >= 5  -- Minimum threshold
ORDER BY recent_interactions DESC
LIMIT 50;

-- Suggested Index:
-- CREATE INDEX idx_interactions_movie_created ON user_movie_interactions(movie_id, created_at DESC);


-- ----------------------------------------------------------------------------
-- QUERY 9: Genre Popularity Shifts Over Time
-- ----------------------------------------------------------------------------
-- Business Value: Track changing tastes to adjust content strategy
-- Technique: LAG for period comparison, PARTITION BY genre
--
-- Output Schema:
--   month DATE                - Calendar month
--   genre_name VARCHAR        - Genre name
--   interaction_count INT     - Total interactions that month
--   prev_month_count INT      - Previous month interactions
--   month_over_month_change PCTG - Change percentage
--   genre_trend VARCHAR       - Rising/Falling/Stable
-- ----------------------------------------------------------------------------

WITH monthly_genre_activity AS (
    SELECT
        DATE_TRUNC('month', umi.created_at)::DATE AS month,
        g.name AS genre_name,
        COUNT(*) AS interaction_count,
        COUNT(DISTINCT umi.user_id) AS unique_users
    FROM user_movie_interactions umi
    JOIN movie_genres mg ON umi.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.id
    WHERE umi.created_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', umi.created_at), g.name
),
genre_trends AS (
    SELECT
        month,
        genre_name,
        interaction_count,
        unique_users,
        -- Previous month's count using LAG
        LAG(interaction_count, 1) OVER (
            PARTITION BY genre_name
            ORDER BY month
        ) AS prev_month_count,
        -- 3-month moving average
        ROUND(
            AVG(interaction_count) OVER (
                PARTITION BY genre_name
                ORDER BY month
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ), 2
        ) AS three_month_avg,
        -- Rank within each month
        RANK() OVER (
            PARTITION BY month
            ORDER BY interaction_count DESC
        ) AS monthly_rank
    FROM monthly_genre_activity
)
SELECT
    month,
    genre_name,
    interaction_count,
    prev_month_count,
    three_month_avg,
    unique_users,
    monthly_rank,
    -- Month-over-month change
    ROUND(
        (interaction_count - prev_month_count)::NUMERIC / NULLIF(prev_month_count, 0) * 100, 2
    ) AS mom_change_pct,
    -- Trend classification
    CASE
        WHEN interaction_count > prev_month_count * 1.1 THEN 'Rising'
        WHEN interaction_count < prev_month_count * 0.9 THEN 'Falling'
        ELSE 'Stable'
    END AS genre_trend,
    -- Rank change from previous month
    monthly_rank - LAG(monthly_rank, 1) OVER (
        PARTITION BY genre_name
        ORDER BY month
    ) AS rank_change
FROM genre_trends
WHERE prev_month_count IS NOT NULL
ORDER BY month DESC, interaction_count DESC;


-- ----------------------------------------------------------------------------
-- QUERY 10: Movie Performance with 7-Day and 30-Day Moving Averages
-- ----------------------------------------------------------------------------
-- Business Value: Smooth out daily noise to identify true performance trends
-- Technique: Window frames with ROWS BETWEEN for moving averages
--
-- Output Schema:
--   activity_date DATE        - Calendar date
--   movie_id INT              - Movie identifier
--   title VARCHAR             - Movie title
--   daily_interactions INT    - Interactions on that day
--   avg_7day NUMERIC          - 7-day moving average
--   avg_30day NUMERIC         - 30-day moving average
--   performance_signal VARCHAR - Hot/Normal/Cold
-- ----------------------------------------------------------------------------

WITH daily_movie_stats AS (
    SELECT
        DATE(umi.created_at) AS activity_date,
        m.id AS movie_id,
        m.title,
        COUNT(*) AS daily_interactions,
        COUNT(CASE WHEN umi.interaction_type = 'watch' THEN 1 END) AS daily_watches
    FROM user_movie_interactions umi
    JOIN movies m ON umi.movie_id = m.id
    WHERE umi.created_at >= CURRENT_DATE - INTERVAL '60 days'
    GROUP BY DATE(umi.created_at), m.id, m.title
),
movie_moving_averages AS (
    SELECT
        activity_date,
        movie_id,
        title,
        daily_interactions,
        daily_watches,
        -- 7-day moving average
        ROUND(
            AVG(daily_interactions) OVER (
                PARTITION BY movie_id
                ORDER BY activity_date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2
        ) AS avg_7day,
        -- 30-day moving average
        ROUND(
            AVG(daily_interactions) OVER (
                PARTITION BY movie_id
                ORDER BY activity_date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ), 2
        ) AS avg_30day,
        -- Standard deviation for anomaly detection
        STDDEV(daily_interactions) OVER (
            PARTITION BY movie_id
            ORDER BY activity_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS stddev_30day
    FROM daily_movie_stats
)
SELECT
    activity_date,
    movie_id,
    title,
    daily_interactions,
    daily_watches,
    avg_7day,
    avg_30day,
    ROUND(stddev_30day::NUMERIC, 2) AS stddev_30day,
    -- Performance signal based on comparison to moving averages
    CASE
        WHEN daily_interactions > avg_30day + (2 * COALESCE(stddev_30day, 0)) THEN 'Hot'
        WHEN daily_interactions < avg_30day - stddev_30day THEN 'Cold'
        ELSE 'Normal'
    END AS performance_signal,
    -- Short-term vs long-term trend
    CASE
        WHEN avg_7day > avg_30day * 1.2 THEN 'Accelerating'
        WHEN avg_7day < avg_30day * 0.8 THEN 'Decelerating'
        ELSE 'Steady'
    END AS trend_direction
FROM movie_moving_averages
WHERE activity_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY activity_date DESC, daily_interactions DESC;


-- ============================================================================
-- SECTION 4: ADVANCED ANALYTICS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 11: User Similarity for Collaborative Filtering
-- ----------------------------------------------------------------------------
-- Business Value: Foundation for user-user collaborative recommendations
-- Technique: Self-join, window functions for similarity calculation
--
-- Output Schema:
--   user_1 INT                - First user
--   user_2 INT                - Second user
--   common_movies INT         - Movies both interacted with
--   agreement_rate PCTG       - Same interaction type rate
--   similarity_score NUMERIC  - Composite similarity
-- ----------------------------------------------------------------------------

WITH user_interactions AS (
    SELECT
        user_id,
        movie_id,
        interaction_type,
        rating
    FROM user_movie_interactions
    WHERE created_at >= CURRENT_DATE - INTERVAL '180 days'
),
user_pairs AS (
    SELECT
        ui1.user_id AS user_1,
        ui2.user_id AS user_2,
        ui1.movie_id,
        ui1.interaction_type AS type_1,
        ui2.interaction_type AS type_2,
        ui1.rating AS rating_1,
        ui2.rating AS rating_2,
        -- Agreement: same interaction type
        CASE WHEN ui1.interaction_type = ui2.interaction_type THEN 1 ELSE 0 END AS agreement
    FROM user_interactions ui1
    JOIN user_interactions ui2
        ON ui1.movie_id = ui2.movie_id
        AND ui1.user_id < ui2.user_id  -- Avoid duplicates
),
similarity_scores AS (
    SELECT
        user_1,
        user_2,
        COUNT(*) AS common_movies,
        SUM(agreement) AS agreements,
        ROUND(SUM(agreement)::NUMERIC / COUNT(*) * 100, 2) AS agreement_rate,
        -- Correlation of ratings (Pearson-like)
        CORR(rating_1, rating_2) AS rating_correlation
    FROM user_pairs
    GROUP BY user_1, user_2
    HAVING COUNT(*) >= 5  -- Minimum overlap threshold
)
SELECT
    user_1,
    user_2,
    common_movies,
    agreements,
    agreement_rate,
    ROUND(COALESCE(rating_correlation, 0)::NUMERIC, 3) AS rating_correlation,
    -- Composite similarity score
    ROUND(
        (agreement_rate * 0.6) +
        (COALESCE(rating_correlation, 0) * 40) +
        (LEAST(common_movies, 50)::NUMERIC / 50 * 20)  -- Bonus for more overlap
    , 2) AS similarity_score,
    -- Rank similar users for each user
    ROW_NUMBER() OVER (
        PARTITION BY user_1
        ORDER BY
            (agreement_rate * 0.6) +
            (COALESCE(rating_correlation, 0) * 40) +
            (LEAST(common_movies, 50)::NUMERIC / 50 * 20) DESC
    ) AS similarity_rank
FROM similarity_scores
ORDER BY similarity_score DESC
LIMIT 1000;


-- ----------------------------------------------------------------------------
-- QUERY 12: Content Recommendation Conversion by Source
-- ----------------------------------------------------------------------------
-- Business Value: Understand which recommendation sources drive conversions
-- Technique: JSON extraction, multiple aggregations, ranking
--
-- Output Schema:
--   recommendation_source VARCHAR - Algorithm or hybrid source
--   total_shown INT               - Recommendations displayed
--   conversion_count INT          - Led to watch/favorite
--   conversion_rate PCTG          - Success rate
--   avg_time_to_conversion HOURS  - Average decision time
-- ----------------------------------------------------------------------------

WITH recommendation_outcomes AS (
    SELECT
        rs.id AS session_id,
        rs.user_id,
        rs.created_at AS recommendation_time,
        -- Extract individual algorithm contributions
        CASE
            WHEN rs.claude_recommendations IS NOT NULL THEN 'Claude'
            WHEN rs.openai_recommendations IS NOT NULL THEN 'OpenAI'
            WHEN rs.gemini_recommendations IS NOT NULL THEN 'Gemini'
            WHEN rs.collaborative_recommendations IS NOT NULL THEN 'Collaborative'
            WHEN rs.content_based_recommendations IS NOT NULL THEN 'Content-Based'
            ELSE 'Hybrid'
        END AS primary_source,
        rs.recommendations_shown,
        rf.action,
        rf.movie_id,
        rf.created_at AS action_time,
        -- Time to action in hours
        EXTRACT(EPOCH FROM (rf.created_at - rs.created_at)) / 3600 AS hours_to_action
    FROM recommendation_sessions rs
    LEFT JOIN recommendation_feedback rf ON rs.id = rf.session_id
    WHERE rs.created_at >= CURRENT_DATE - INTERVAL '30 days'
),
source_performance AS (
    SELECT
        primary_source,
        COUNT(DISTINCT session_id) AS total_sessions,
        SUM(recommendations_shown) AS total_shown,
        COUNT(CASE WHEN action IN ('watch', 'favorite') THEN 1 END) AS conversion_count,
        COUNT(CASE WHEN action = 'pass' THEN 1 END) AS pass_count,
        AVG(hours_to_action) FILTER (WHERE action IN ('watch', 'favorite')) AS avg_hours_to_conversion
    FROM recommendation_outcomes
    GROUP BY primary_source
)
SELECT
    primary_source AS recommendation_source,
    total_sessions,
    total_shown,
    conversion_count,
    pass_count,
    ROUND(conversion_count::NUMERIC / NULLIF(total_shown, 0) * 100, 2) AS conversion_rate,
    ROUND(avg_hours_to_conversion::NUMERIC, 2) AS avg_hours_to_conversion,
    -- Rank by conversion rate
    RANK() OVER (ORDER BY
        conversion_count::NUMERIC / NULLIF(total_shown, 0) DESC
    ) AS conversion_rank,
    -- Rank by volume
    RANK() OVER (ORDER BY total_shown DESC) AS volume_rank
FROM source_performance
WHERE total_shown >= 10
ORDER BY conversion_rate DESC;


-- ----------------------------------------------------------------------------
-- QUERY 13: Mood-Based Recommendation Effectiveness
-- ----------------------------------------------------------------------------
-- Business Value: Optimize mood-based personalization
-- Technique: Partition by mood, comparative analytics
--
-- Output Schema:
--   mood VARCHAR               - User mood at recommendation time
--   session_count INT          - Sessions with this mood
--   avg_recommendations INT    - Average recommendations per session
--   watch_rate PCTG            - Conversion to watch
--   top_genre VARCHAR          - Most successful genre for mood
-- ----------------------------------------------------------------------------

WITH mood_sessions AS (
    SELECT
        rs.mood,
        rs.id AS session_id,
        rs.user_id,
        rs.recommendations_shown,
        rf.action,
        rf.movie_id
    FROM recommendation_sessions rs
    LEFT JOIN recommendation_feedback rf ON rs.id = rf.session_id
    WHERE rs.mood IS NOT NULL
      AND rs.created_at >= CURRENT_DATE - INTERVAL '60 days'
),
mood_genre_performance AS (
    SELECT
        ms.mood,
        g.name AS genre_name,
        COUNT(*) AS total_interactions,
        COUNT(CASE WHEN ms.action = 'watch' THEN 1 END) AS watches,
        ROUND(
            COUNT(CASE WHEN ms.action = 'watch' THEN 1 END)::NUMERIC /
            NULLIF(COUNT(*), 0) * 100, 2
        ) AS genre_watch_rate,
        -- Rank genres within each mood
        ROW_NUMBER() OVER (
            PARTITION BY ms.mood
            ORDER BY COUNT(CASE WHEN ms.action = 'watch' THEN 1 END) DESC
        ) AS genre_rank
    FROM mood_sessions ms
    JOIN movie_genres mg ON ms.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.id
    GROUP BY ms.mood, g.name
),
mood_metrics AS (
    SELECT
        mood,
        COUNT(DISTINCT session_id) AS session_count,
        SUM(recommendations_shown) AS total_shown,
        COUNT(CASE WHEN action = 'watch' THEN 1 END) AS watch_count,
        COUNT(CASE WHEN action = 'pass' THEN 1 END) AS pass_count,
        AVG(recommendations_shown) AS avg_recommendations_per_session
    FROM mood_sessions
    GROUP BY mood
)
SELECT
    mm.mood,
    mm.session_count,
    ROUND(mm.avg_recommendations_per_session::NUMERIC, 1) AS avg_recommendations,
    mm.watch_count,
    mm.pass_count,
    ROUND(mm.watch_count::NUMERIC / NULLIF(mm.total_shown, 0) * 100, 2) AS watch_rate,
    mgp.genre_name AS top_genre_for_mood,
    mgp.genre_watch_rate AS top_genre_watch_rate,
    -- Rank moods by overall effectiveness
    RANK() OVER (ORDER BY
        mm.watch_count::NUMERIC / NULLIF(mm.total_shown, 0) DESC
    ) AS mood_effectiveness_rank
FROM mood_metrics mm
LEFT JOIN mood_genre_performance mgp
    ON mm.mood = mgp.mood AND mgp.genre_rank = 1
WHERE mm.session_count >= 5
ORDER BY watch_rate DESC;


-- ============================================================================
-- BONUS QUERY: Comprehensive User Profile Analytics
-- ============================================================================
-- Business Value: Full user behavioral profile for personalization
-- Technique: Complex CTE chain, multiple window functions, JSON aggregation
-- ----------------------------------------------------------------------------

WITH user_base AS (
    SELECT
        u.id AS user_id,
        u.username,
        u.created_at AS signup_date,
        u.is_onboarded,
        DATE_PART('day', CURRENT_TIMESTAMP - u.created_at) AS account_age_days,
        DATE_PART('day', CURRENT_TIMESTAMP - u.last_login) AS days_since_login
    FROM users u
    WHERE u.is_active = true
),
user_interaction_summary AS (
    SELECT
        user_id,
        COUNT(*) AS total_interactions,
        COUNT(CASE WHEN interaction_type = 'watch' THEN 1 END) AS watch_count,
        COUNT(CASE WHEN interaction_type = 'pass' THEN 1 END) AS pass_count,
        COUNT(CASE WHEN interaction_type = 'favorite' THEN 1 END) AS favorite_count,
        COUNT(CASE WHEN interaction_type = 'rating' THEN 1 END) AS rating_count,
        AVG(rating) FILTER (WHERE rating IS NOT NULL) AS avg_rating,
        MIN(created_at) AS first_interaction,
        MAX(created_at) AS last_interaction
    FROM user_movie_interactions
    GROUP BY user_id
),
user_genre_preferences AS (
    SELECT
        umi.user_id,
        -- Aggregate top genres as JSON
        JSONB_AGG(
            JSONB_BUILD_OBJECT('genre', g.name, 'count', genre_counts.cnt)
            ORDER BY genre_counts.cnt DESC
        ) FILTER (WHERE genre_counts.rn <= 3) AS top_genres
    FROM user_movie_interactions umi
    JOIN movie_genres mg ON umi.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.id
    JOIN (
        SELECT
            umi2.user_id,
            g2.name,
            COUNT(*) AS cnt,
            ROW_NUMBER() OVER (PARTITION BY umi2.user_id ORDER BY COUNT(*) DESC) AS rn
        FROM user_movie_interactions umi2
        JOIN movie_genres mg2 ON umi2.movie_id = mg2.movie_id
        JOIN genres g2 ON mg2.genre_id = g2.id
        WHERE umi2.interaction_type IN ('watch', 'favorite')
        GROUP BY umi2.user_id, g2.name
    ) genre_counts ON umi.user_id = genre_counts.user_id AND g.name = genre_counts.name
    GROUP BY umi.user_id
),
user_session_stats AS (
    SELECT
        user_id,
        COUNT(*) AS total_sessions,
        AVG(recommendations_shown) AS avg_recs_per_session,
        MODE() WITHIN GROUP (ORDER BY mood) AS most_common_mood,
        MODE() WITHIN GROUP (ORDER BY watching_with) AS most_common_context
    FROM recommendation_sessions
    GROUP BY user_id
)
SELECT
    ub.user_id,
    ub.username,
    ub.signup_date,
    ub.account_age_days,
    ub.days_since_login,
    ub.is_onboarded,
    -- Interaction metrics
    COALESCE(uis.total_interactions, 0) AS total_interactions,
    COALESCE(uis.watch_count, 0) AS watches,
    COALESCE(uis.favorite_count, 0) AS favorites,
    ROUND(COALESCE(uis.avg_rating, 0)::NUMERIC, 2) AS avg_rating,
    -- Engagement rate
    ROUND(
        COALESCE(uis.watch_count, 0)::NUMERIC /
        NULLIF(COALESCE(uis.total_interactions, 0), 0) * 100, 2
    ) AS watch_rate,
    -- Preferences
    ugp.top_genres,
    uss.most_common_mood,
    uss.most_common_context,
    ROUND(COALESCE(uss.avg_recs_per_session, 0)::NUMERIC, 1) AS avg_recs_per_session,
    -- User segment
    CASE
        WHEN uis.total_interactions >= 100 THEN 'Power User'
        WHEN uis.total_interactions >= 30 THEN 'Active'
        WHEN uis.total_interactions >= 10 THEN 'Casual'
        WHEN uis.total_interactions >= 1 THEN 'New'
        ELSE 'Inactive'
    END AS user_segment,
    -- Churn risk
    CASE
        WHEN ub.days_since_login > 30 THEN 'High'
        WHEN ub.days_since_login > 14 THEN 'Medium'
        ELSE 'Low'
    END AS churn_risk,
    -- Engagement percentile
    NTILE(100) OVER (ORDER BY COALESCE(uis.total_interactions, 0)) AS engagement_percentile
FROM user_base ub
LEFT JOIN user_interaction_summary uis ON ub.user_id = uis.user_id
LEFT JOIN user_genre_preferences ugp ON ub.user_id = ugp.user_id
LEFT JOIN user_session_stats uss ON ub.user_id = uss.user_id
ORDER BY COALESCE(uis.total_interactions, 0) DESC;


-- ============================================================================
-- RECOMMENDED INDEXES FOR OPTIMAL PERFORMANCE
-- ============================================================================
--
-- User engagement queries:
-- CREATE INDEX idx_interactions_user_created ON user_movie_interactions(user_id, created_at DESC);
-- CREATE INDEX idx_interactions_created_at ON user_movie_interactions(created_at);
-- CREATE INDEX idx_interactions_type ON user_movie_interactions(interaction_type);
--
-- Movie popularity queries:
-- CREATE INDEX idx_interactions_movie_created ON user_movie_interactions(movie_id, created_at DESC);
-- CREATE INDEX idx_movies_release_year ON movies(release_year);
-- CREATE INDEX idx_movies_popularity ON movies(popularity DESC);
--
-- Recommendation analysis:
-- CREATE INDEX idx_sessions_user_created ON recommendation_sessions(user_id, created_at DESC);
-- CREATE INDEX idx_sessions_mood ON recommendation_sessions(mood);
-- CREATE INDEX idx_feedback_session ON recommendation_feedback(session_id);
-- CREATE INDEX idx_feedback_action ON recommendation_feedback(action);
--
-- Genre analysis:
-- CREATE INDEX idx_movie_genres_movie ON movie_genres(movie_id);
-- CREATE INDEX idx_movie_genres_genre ON movie_genres(genre_id);
--
-- ============================================================================
