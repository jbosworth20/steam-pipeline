from __future__ import annotations

import logging
import time
from typing import Any

import requests

from . import config

log = logging.getLogger(__name__)

_session = requests.Session()
_session.headers.update({"User-Agent": "steam-pipeline"})


def _get(url: str, *, params: dict[str, Any] | None = None, timeout: int) -> Any:
    resp = _session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_top_games(num_games: int, timeout: int) -> list[dict[str, Any]]:
    log.info("fetching top %d games from SteamSpy", num_games)
    payload = _get(config.STEAMSPY_URL, params={"request": "top100in2weeks"}, timeout=timeout)
    return list(payload.values())[:num_games]


def fetch_current_players(appid: int, timeout: int) -> int | None:
    payload = _get(config.STEAM_CURRENT_PLAYERS_URL, params={"appid": appid}, timeout=timeout)
    response = payload.get("response", {})
    if response.get("result") != 1:
        return None
    return response.get("player_count")


def extract_all(cfg: config.Config) -> dict[str, list[dict[str, Any]]]:
    games = fetch_top_games(cfg.num_games, cfg.request_timeout)
    snapshot_ts = int(time.time())

    player_counts: list[dict[str, Any]] = []

    for i, game in enumerate(games):
        appid = int(game["appid"])
        if i > 0:
            time.sleep(cfg.steamspy_min_interval)

        players = None
        try:
            players = fetch_current_players(appid, cfg.request_timeout)
            if players is not None:
                player_counts.append(
                    {"appid": appid, "snapshot_ts": snapshot_ts, "concurrent_players": players}
                )
        except requests.RequestException:
            log.warning("player count failed for appid=%s", appid, exc_info=True)

        log.info("appid=%s players=%s", appid, players)

    return {"games": games, "player_counts": player_counts}
