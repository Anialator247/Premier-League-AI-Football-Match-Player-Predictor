import numpy as np

from pl_analytics.compare_models import run
from pl_analytics.split import load_split

from .synthetic import write_fake_raw_dir


def test_split_is_chronological(tmp_path):
    write_fake_raw_dir(tmp_path / "raw")
    train, test, feats = load_split(tmp_path / "raw", test_fraction=0.2)
    assert train["Date"].max() <= test["Date"].min()
    assert not train[feats].isna().any().any()


def test_compare_models_end_to_end(tmp_path):
    write_fake_raw_dir(tmp_path / "raw")
    out = run(tmp_path / "raw", tmp_path / "out")
    names = set(out["results"]["model"])
    assert {"Class frequencies", "Logistic Regression", "Random Forest", "Bet365 odds"} <= names
    assert np.isclose(out["importance"]["importance"].sum(), 1.0, atol=0.01)
    for f in ["model_comparison.csv", "feature_importance.csv", "calibration.png",
              "test_predictions_random_forest.csv", "test_predictions_logistic_regression.csv"]:
        assert (tmp_path / "out" / f).exists()
