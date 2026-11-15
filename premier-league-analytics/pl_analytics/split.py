"""One shared, chronological train/test split so every model is judged on the same matches."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data import load_matches
from .features import add_form_features, feature_columns


def load_split(raw_dir=Path("data/raw"), test_fraction=0.2, window=5):
    """Return (train, test, feature_names). Train is the past, test is the most recent matches."""
    data = add_form_features(load_matches(raw_dir), window=window)
    feats = feature_columns(data)
    data = data.dropna(subset=feats).reset_index(drop=True)
    cut = int(len(data) * (1 - test_fraction))
    return data.iloc[:cut], data.iloc[cut:], feats
