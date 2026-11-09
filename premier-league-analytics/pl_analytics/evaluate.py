"""Metrics and baselines for match outcome prediction."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

CLASSES = ["A", "D", "H"]  # away win, draw, home win (alphabetical, matches sklearn's classes_)


def bookmaker_probs(df: pd.DataFrame) -> np.ndarray | None:
    """Bet365 odds converted to probabilities with the bookmaker's margin removed."""
    cols = ["B365A", "B365D", "B365H"]
    if not all(c in df.columns for c in cols) or df[cols].isna().any().any():
        return None
    implied = 1.0 / df[cols].to_numpy(dtype=float)
    return implied / implied.sum(axis=1, keepdims=True)


def summarise(y_true, proba: np.ndarray, label: str) -> dict:
    pred = np.array(CLASSES)[proba.argmax(axis=1)]
    return {
        "model": label,
        "accuracy": accuracy_score(y_true, pred),
        "log_loss": log_loss(y_true, proba, labels=CLASSES),
    }
