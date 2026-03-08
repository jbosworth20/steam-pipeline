from __future__ import annotations

import argparse
import logging

from . import config, extract, load, marts, transform

log = logging.getLogger(__name__)


def run(cfg: config.Config | None = None) -> dict[str, int]:
    cfg = cfg or config.Config.from_env()
    log.info(
        "starting run: num_games=%d target=%s",
        cfg.num_games,
        cfg.duckdb_path,
    )

    raw = extract.extract_all(cfg)
    dim_games = transform.build_dim_games(raw["games"])
    fact_player_counts = transform.build_fact_player_counts(raw["player_counts"])

    load.load_warehouse(cfg, dim_games, fact_player_counts)

    con = load.connect(cfg)
    try:
        marts.build_marts(con)
    finally:
        con.close()

    metrics = {
        "games": len(dim_games),
        "player_count_snapshots": len(fact_player_counts),
    }
    log.info("run complete: %s", metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Steam data pipeline.")
    parser.add_argument("--games", type=int, help="number of games to ingest")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    cfg = config.Config.from_env(num_games=args.games)
    metrics = run(cfg)

    print("\nRun summary:")
    for key, value in metrics.items():
        print(f"  {key:>24}: {value}")


if __name__ == "__main__":
    main()
