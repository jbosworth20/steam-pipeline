from __future__ import annotations

import re

import pandas as pd

_NUMBER = re.compile(r"[\d,]+")


def parse_owners_midpoint(owners: str | None) -> int | None:
    if not owners:
        return None
    nums = [int(n.replace(",", "")) for n in _NUMBER.findall(owners)]
    return sum(nums) // len(nums) if nums else None


def build_dim_games(raw_games: list[dict]) -> pd.DataFrame:
    rows = []
    for g in raw_games:
        positive = int(g.get("positive") or 0)
        negative = int(g.get("negative") or 0)
        total = positive + negative
        price_cents = int(g.get("price") or 0)
        rows.append(
            {
                "appid": int(g["appid"]),
                "name": g.get("name"),
                "developer": g.get("developer") or None,
                "publisher": g.get("publisher") or None,
                "price_usd": round(price_cents / 100, 2),
                "is_free": price_cents == 0,
                "owners_estimate": parse_owners_midpoint(g.get("owners")),
                "positive_reviews": positive,
                "negative_reviews": negative,
                "total_reviews": total,
                "positive_ratio": round(positive / total, 4) if total else None,
                "avg_playtime_forever_min": int(g.get("average_forever") or 0),
                "median_playtime_forever_min": int(g.get("median_forever") or 0),
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset="appid").reset_index(drop=True)


def build_fact_player_counts(raw_counts: list[dict]) -> pd.DataFrame:
    columns = ["appid", "snapshot_ts", "snapshot_at", "concurrent_players"]
    if not raw_counts:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(raw_counts)
    df["appid"] = df["appid"].astype(int)
    df["concurrent_players"] = df["concurrent_players"].astype(int)
    df["snapshot_at"] = pd.to_datetime(df["snapshot_ts"], unit="s", utc=True)
    return df[columns]
