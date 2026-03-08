# steam-pipeline

A small CLI that pulls Steam popularity and rating data into DuckDB.

## What it does

Each run gets top games from SteamSpy, current player counts from Steam, and
Steam rating summaries from positive/negative review totals. Raw files are
written to `data/raw/`, then loaded into `data/steam.duckdb`.

Tables:

- `dim_games`
- `fact_player_counts`

The CLI also creates a few `mart_*` views for quick analysis.

## Architecture

```
SteamSpy / Steam APIs
        |
        v
data/raw/**  Parquet
        |
        v
data/steam.duckdb
```

## Quickstart

Install `uv` if you do not already have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
uv sync

uv run steam-pipeline --games 5
```

That writes raw Parquet files under `data/raw/` and updates `data/steam.duckdb`.

## Configuration

Settings come from the environment:

| Variable                  | Default             | Purpose                              |
| ------------------------- | ------------------- | ------------------------------------ |
| `STEAM_NUM_GAMES`         | `25`                | number of top games to ingest        |
| `STEAM_DUCKDB_PATH`       | `data/steam.duckdb` | warehouse path                      |
