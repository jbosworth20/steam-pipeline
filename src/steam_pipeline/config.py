from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

STEAMSPY_URL = "https://steamspy.com/api.php"
STEAM_CURRENT_PLAYERS_URL = (
    "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


@dataclass(frozen=True)
class Config:
    num_games: int = 25
    duckdb_path: str = str(DATA_DIR / "steam.duckdb")
    request_timeout: int = 20
    steamspy_min_interval: float = 1.0

    @classmethod
    def from_env(cls, **overrides: int | None) -> Config:
        cfg = cls(
            num_games=_env_int("STEAM_NUM_GAMES", cls.num_games),
            duckdb_path=os.environ.get("STEAM_DUCKDB_PATH", cls.duckdb_path),
            request_timeout=_env_int("STEAM_HTTP_TIMEOUT", cls.request_timeout),
        )
        return replace(cfg, **{k: v for k, v in overrides.items() if v is not None})
