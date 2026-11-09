"""Fake league data in the same CSV format as football-data.co.uk, for tests."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TEAMS = [f"Team {c}" for c in "ABCDEFGHIJKLMNOPQRST"]  # 20 teams, like the Premier League


def write_fake_season(path: Path, start_year: int, seed: int, old_date_format: bool = False) -> None:
    rng = np.random.default_rng(seed)
    strength = dict(zip(TEAMS, rng.normal(0, 0.4, len(TEAMS))))
    rows, day = [], pd.Timestamp(f"{start_year}-08-10")
    fixtures = [(h, a) for h in TEAMS for a in TEAMS if h != a]
    rng.shuffle(fixtures)
    for i, (h, a) in enumerate(fixtures):
        hg = rng.poisson(np.exp(0.25 + strength[h] - 0.5 * strength[a]))
        ag = rng.poisson(np.exp(0.0 + strength[a] - 0.5 * strength[h]))
        ftr = "H" if hg > ag else "A" if ag > hg else "D"
        odds = 1.05 / np.array([0.45, 0.27, 0.28])
        date = day + pd.Timedelta(days=i // 10 * 3)
        rows.append({
            "Date": date.strftime("%d/%m/%y" if old_date_format else "%d/%m/%Y"),
            "HomeTeam": h, "AwayTeam": a, "FTHG": hg, "FTAG": ag, "FTR": ftr,
            "HS": hg * 4 + rng.integers(3, 9), "AS": ag * 4 + rng.integers(3, 9),
            "HST": hg + rng.integers(1, 4), "AST": ag + rng.integers(1, 4),
            "B365H": odds[0], "B365D": odds[1], "B365A": odds[2],
        })
    df = pd.DataFrame(rows)
    df.loc[len(df)] = [None] * len(df.columns)  # real files often end with a blank row
    df.to_csv(path, index=False)


def write_fake_raw_dir(raw_dir: Path, n_seasons: int = 4) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for k in range(n_seasons):
        year = 2019 + k
        code = f"{year % 100:02d}{(year + 1) % 100:02d}"
        write_fake_season(raw_dir / f"E0_{code}.csv", year, seed=k, old_date_format=(k == 0))
