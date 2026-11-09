"""Baseline: multinomial Logistic Regression on rolling form features.

Run:  python -m pl_analytics.train_baseline
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import load_matches
from .evaluate import CLASSES, bookmaker_probs, summarise
from .features import add_form_features, feature_columns


def run(raw_dir=Path("data/raw"), out_dir=Path("outputs"), test_fraction=0.2, window=5) -> dict:
    matches = load_matches(raw_dir)
    data = add_form_features(matches, window=window)
    feats = feature_columns(data)
    data = data.dropna(subset=feats).reset_index(drop=True)

    # Chronological split: train on the past, test on the most recent matches.
    cut = int(len(data) * (1 - test_fraction))
    train, test = data.iloc[:cut], data.iloc[cut:]

    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model.fit(train[feats], train["FTR"])
    assert list(model.classes_) == CLASSES
    proba = model.predict_proba(test[feats])

    # Baselines to beat: the training-set class frequencies, and the bookmakers.
    prior = train["FTR"].value_counts(normalize=True).reindex(CLASSES).to_numpy()
    results = [
        summarise(test["FTR"], np.tile(prior, (len(test), 1)), "Class frequencies"),
        summarise(test["FTR"], proba, "Logistic Regression"),
    ]
    book = bookmaker_probs(test)
    if book is not None:
        results.append(summarise(test["FTR"], book, "Bet365 odds"))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preds = test[["Date", "HomeTeam", "AwayTeam", "FTR"]].copy()
    preds["Predicted"] = np.array(CLASSES)[proba.argmax(axis=1)]
    for i, c in enumerate(CLASSES):
        preds[f"P_{c}"] = proba[:, i].round(3)
    preds.to_csv(out_dir / "test_predictions.csv", index=False)

    table = pd.DataFrame(results).round(3)
    print(f"Train: {len(train)} matches | Test: {len(test)} matches "
          f"({test['Date'].min():%Y-%m-%d} to {test['Date'].max():%Y-%m-%d})")
    print(table.to_string(index=False))
    return {"results": table, "predictions": preds, "n_train": len(train), "n_test": len(test)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--out-dir", type=Path, default=Path("outputs"))
    p.add_argument("--test-fraction", type=float, default=0.2)
    p.add_argument("--window", type=int, default=5, help="number of previous matches in the form window")
    a = p.parse_args()
    run(a.raw_dir, a.out_dir, a.test_fraction, a.window)


if __name__ == "__main__":
    main()
