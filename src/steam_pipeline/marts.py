from __future__ import annotations

import logging

import duckdb

log = logging.getLogger(__name__)

MART_DEFINITIONS: list[tuple[str, str]] = [
    (
        "mart_game_leaderboard",
        """
        CREATE OR REPLACE VIEW mart_game_leaderboard AS
        WITH latest AS (
            SELECT appid, concurrent_players,
                   ROW_NUMBER() OVER (PARTITION BY appid ORDER BY snapshot_ts DESC) AS rn
            FROM fact_player_counts
        )
        SELECT g.appid, g.name, g.developer,
               l.concurrent_players,
               g.price_usd, g.is_free,
               g.owners_estimate,
               g.total_reviews, g.positive_ratio
        FROM dim_games g
        LEFT JOIN latest l ON g.appid = l.appid AND l.rn = 1
        ORDER BY l.concurrent_players DESC NULLS LAST
        """,
    ),
    (
        "mart_rating_player_ratio",
        """
        CREATE OR REPLACE VIEW mart_rating_player_ratio AS
        WITH latest AS (
            SELECT appid, concurrent_players,
                   ROW_NUMBER() OVER (PARTITION BY appid ORDER BY snapshot_ts DESC) AS rn
            FROM fact_player_counts
        )
        SELECT g.appid, g.name,
               g.positive_ratio, g.total_reviews,
               l.concurrent_players,
               ROUND(g.positive_ratio / NULLIF(l.concurrent_players, 0) * 100000, 2) AS score
        FROM dim_games g
        JOIN latest l ON g.appid = l.appid AND l.rn = 1
        WHERE g.total_reviews >= 500
          AND g.positive_ratio >= 0.85
          AND l.concurrent_players > 0
        ORDER BY score DESC
        """,
    ),
    (
        "mart_player_momentum",
        """
        CREATE OR REPLACE VIEW mart_player_momentum AS
        WITH ranked AS (
            SELECT appid,
                   FIRST_VALUE(concurrent_players) OVER w AS first_players,
                   LAST_VALUE(concurrent_players) OVER w  AS last_players,
                   COUNT(*) OVER (PARTITION BY appid)      AS n_snapshots
            FROM fact_player_counts
            WINDOW w AS (
                PARTITION BY appid ORDER BY snapshot_at
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            )
        )
        SELECT DISTINCT
               r.appid, g.name, r.n_snapshots,
               r.first_players, r.last_players,
               r.last_players - r.first_players AS abs_change,
               ROUND((r.last_players - r.first_players)
                     / NULLIF(r.first_players, 0) * 100, 1) AS pct_change
        FROM ranked r
        JOIN dim_games g ON r.appid = g.appid
        ORDER BY pct_change DESC NULLS LAST
        """,
    ),
]


def build_marts(con: duckdb.DuckDBPyConnection) -> list[str]:
    for name, sql in MART_DEFINITIONS:
        con.execute(sql)
        log.info("built %s", name)
    return [name for name, _ in MART_DEFINITIONS]
