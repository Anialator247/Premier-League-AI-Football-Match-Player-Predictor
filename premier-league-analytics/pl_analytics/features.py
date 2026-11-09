"""Rolling form features for each team, built so a match never sees its own result."""
from __future__ import annotations

import numpy as np
import pandas as pd

ROLL_COLS = ["pts", "gf", "ga", "shots", "sot"]


def _team_rows(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match (so each match appears twice, once per side)."""
    m = matches.reset_index(drop=True)
    ids = m.index

    def side(team, gf, ga, shots, sot, is_home):
        return pd.DataFrame({
            "match_id": ids, "Date": m["Date"], "team": m[team],
            "gf": m[gf], "ga": m[ga], "shots": m[shots], "sot": m[sot],
            "is_home": is_home,
        })

    rows = pd.concat([
        side("HomeTeam", "FTHG", "FTAG", "HS", "HST", 1),
        side("AwayTeam", "FTAG", "FTHG", "AS", "AST", 0),
    ])
    rows["pts"] = np.select([rows["gf"] > rows["ga"], rows["gf"] == rows["ga"]], [3, 1], 0)
    return rows.sort_values(["team", "Date", "match_id"]).reset_index(drop=True)


def add_form_features(matches: pd.DataFrame, window: int = 5, min_periods: int = 3) -> pd.DataFrame:
    """Add home_*_form and away_*_form: each team's average over its previous `window` matches.

    shift(1) excludes the current match, so there is no data leakage. Form carries across
    seasons. Teams with fewer than `min_periods` earlier matches get NaN.
    """
    rows = _team_rows(matches)
    form = rows.groupby("team")[ROLL_COLS].transform(
        lambda s: s.shift(1).rolling(window, min_periods=min_periods).mean()
    )
    form.columns = [f"{c}_form" for c in ROLL_COLS]
    rows = pd.concat([rows, form], axis=1)

    home = rows[rows["is_home"] == 1].set_index("match_id")[list(form.columns)].add_prefix("home_")
    away = rows[rows["is_home"] == 0].set_index("match_id")[list(form.columns)].add_prefix("away_")
    return matches.reset_index(drop=True).join(home).join(away)


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(("home_", "away_")) and c.endswith("_form")]
