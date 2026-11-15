"""Train Logistic Regression and Random Forest on the same split and compare them.

Run:  python -m pl_analytics.compare_models

Writes to outputs/: model_comparison.csv, test_predictions_<model>.csv,
feature_importance.csv and calibration.png.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to a file, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .evaluate import CLASSES, bookmaker_probs, summarise
from .split import load_split

LABELS = {"A": "Away win", "D": "Draw", "H": "Home win"}


def make_models() -> dict:
    return {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        # min_samples_leaf keeps the trees from memorising a few thousand matches.
        "Random Forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=10, max_features="sqrt",
            n_jobs=-1, random_state=42,
        ),
    }


def plot_calibration(y_test, probas: dict, path: Path, n_bins: int = 8) -> None:
    """Reliability diagram: when a model says 60%, does that outcome happen about 60% of the time?"""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True, sharey=True)
    for i, cls in enumerate(CLASSES):
        ax = axes[i]
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfectly calibrated")
        actual = (np.asarray(y_test) == cls).astype(int)
        for name, proba in probas.items():
            frac, mean_pred = calibration_curve(actual, proba[:, i], n_bins=n_bins, strategy="quantile")
            ax.plot(mean_pred, frac, marker="o", label=name)
        ax.set_title(LABELS[cls])
        ax.set_xlabel("Predicted probability")
        if i == 0:
            ax.set_ylabel("Observed frequency")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(raw_dir=Path("data/raw"), out_dir=Path("outputs"), test_fraction=0.2, window=5) -> dict:
    train, test, feats = load_split(raw_dir, test_fraction, window)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prior = train["FTR"].value_counts(normalize=True).reindex(CLASSES).to_numpy()
    results = [summarise(test["FTR"], np.tile(prior, (len(test), 1)), "Class frequencies")]
    probas = {}

    for name, model in make_models().items():
        model.fit(train[feats], train["FTR"])
        assert list(model.classes_) == CLASSES
        proba = model.predict_proba(test[feats])
        probas[name] = proba
        results.append(summarise(test["FTR"], proba, name))

        preds = test[["Date", "HomeTeam", "AwayTeam", "FTR"]].copy()
        preds["Predicted"] = np.array(CLASSES)[proba.argmax(axis=1)]
        for j, c in enumerate(CLASSES):
            preds[f"P_{c}"] = proba[:, j].round(3)
        preds.to_csv(out_dir / f"test_predictions_{name.lower().replace(' ', '_')}.csv", index=False)

    book = bookmaker_probs(test)
    if book is not None:
        results.append(summarise(test["FTR"], book, "Bet365 odds"))

    table = pd.DataFrame(results).round(3)
    table.to_csv(out_dir / "model_comparison.csv", index=False)

    forest = make_models()["Random Forest"].fit(train[feats], train["FTR"])
    importance = (pd.DataFrame({"feature": feats, "importance": forest.feature_importances_})
                  .sort_values("importance", ascending=False).round(4))
    importance.to_csv(out_dir / "feature_importance.csv", index=False)

    plot_calibration(test["FTR"], probas, out_dir / "calibration.png")

    print(f"Train: {len(train)} matches | Test: {len(test)} matches "
          f"({test['Date'].min():%Y-%m-%d} to {test['Date'].max():%Y-%m-%d})\n")
    print(table.to_string(index=False))
    print("\nTop features (Random Forest):")
    print(importance.head(6).to_string(index=False))
    return {"results": table, "importance": importance, "n_train": len(train), "n_test": len(test)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--out-dir", type=Path, default=Path("outputs"))
    p.add_argument("--test-fraction", type=float, default=0.2)
    p.add_argument("--window", type=int, default=5)
    a = p.parse_args()
    run(a.raw_dir, a.out_dir, a.test_fraction, a.window)


if __name__ == "__main__":
    main()
