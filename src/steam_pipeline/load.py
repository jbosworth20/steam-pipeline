from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from . import config

log = logging.getLogger(__name__)


def connect(cfg: config.Config) -> duckdb.DuckDBPyConnection:
    if not cfg.duckdb_path.startswith("md:"):
        Path(cfg.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(cfg.duckdb_path)


def write_parquet(df: pd.DataFrame, dataset: str) -> Path | None:
    if df.empty:
        return None
    part = config.RAW_DIR / dataset / f"ingest_date={date.today().isoformat()}"
    part.mkdir(parents=True, exist_ok=True)
    out = part / f"{dataset}.parquet"
    df.to_parquet(out, index=False)
    log.info("wrote %d rows -> %s", len(df), out)
    return out


def _create_if_missing(con: duckdb.DuckDBPyConnection, table: str, view: str) -> None:
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM {view} LIMIT 0")


def _insert_new(con: duckdb.DuckDBPyConnection, table: str, join_on: str) -> None:
    con.execute(
        f"""
        INSERT INTO {table}
        SELECT i.* FROM incoming i
        LEFT JOIN {table} t ON {join_on}
        WHERE t.appid IS NULL
        """
    )


def load_warehouse(
    cfg: config.Config,
    dim_games: pd.DataFrame,
    fact_player_counts: pd.DataFrame,
) -> None:
    write_parquet(dim_games, "games")
    write_parquet(fact_player_counts, "player_counts")

    con = connect(cfg)
    try:
        con.register("incoming", dim_games)
        _create_if_missing(con, "dim_games", "incoming")
        con.execute("DELETE FROM dim_games WHERE appid IN (SELECT appid FROM incoming)")
        con.execute("INSERT INTO dim_games SELECT * FROM incoming")
        con.unregister("incoming")

        if not fact_player_counts.empty:
            con.register("incoming", fact_player_counts)
            _create_if_missing(con, "fact_player_counts", "incoming")
            _insert_new(
                con,
                "fact_player_counts",
                "i.appid = t.appid AND i.snapshot_ts = t.snapshot_ts",
            )
            con.unregister("incoming")
        else:
            con.register("incoming", fact_player_counts)
            _create_if_missing(con, "fact_player_counts", "incoming")
            con.unregister("incoming")

        log.info("warehouse load complete -> %s", cfg.duckdb_path)
    finally:
        con.close()
