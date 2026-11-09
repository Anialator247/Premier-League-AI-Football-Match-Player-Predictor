"""Download and load Premier League results from football-data.co.uk."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"

# Columns we use. Shots and bookmaker odds are optional extras.
KEEP = [
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HS", "AS", "HST", "AST", "B365H", "B365D", "B365A",
]


def season_code(start_year: int) -> str:
    """2023 -> '2324', the code football-data.co.uk uses for the 2023/24 season."""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def download_seasons(start_year: int, end_year: int, dest: Path = Path("data/raw")) -> list[Path]:
    """Download one CSV per season (start_year..end_year inclusive). Skips files you already have."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for year in range(start_year, end_year + 1):
        code = season_code(year)
        path = dest / f"E0_{code}.csv"
        if path.exists():
            saved.append(path)
            continue
        try:
            urllib.request.urlretrieve(BASE_URL.format(code=code), path)
        except urllib.error.URLError as exc:
            print(f"Skipped season {code}: {exc}")
            continue
        print(f"Downloaded season {code}")
        saved.append(path)
    return saved


def load_matches(raw_dir: Path = Path("data/raw")) -> pd.DataFrame:
    """Read every E0_*.csv in raw_dir into one chronologically sorted DataFrame."""
    frames = []
    for path in sorted(Path(raw_dir).glob("E0_*.csv")):
        df = pd.read_csv(path, encoding="latin-1")
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"])  # files often end in blank rows
        df = df[[c for c in KEEP if c in df.columns]].copy()
        # Parse per file: older seasons use dd/mm/yy, newer ones dd/mm/yyyy.
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed")
        df["Season"] = path.stem.split("_")[1]
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No E0_*.csv files in {raw_dir}. Run: python -m pl_analytics.download"
        )
    matches = pd.concat(frames, ignore_index=True)
    return matches.sort_values(["Date", "HomeTeam"]).reset_index(drop=True)
