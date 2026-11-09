import numpy as np
import pandas as pd

from pl_analytics.data import load_matches, season_code
from pl_analytics.features import add_form_features, feature_columns
from pl_analytics.train_baseline import run

from .synthetic import write_fake_raw_dir


def _matches(tmp_path):
    write_fake_raw_dir(tmp_path / "raw")
    return load_matches(tmp_path / "raw")


def test_season_code():
    assert season_code(2023) == "2324"
    assert season_code(1999) == "9900"


def test_loader_handles_blank_rows_and_mixed_date_formats(tmp_path):
    m = _matches(tmp_path)
    assert len(m) == 4 * 380
    assert m["Date"].is_monotonic_increasing
    assert m["FTR"].isin(["H", "D", "A"]).all()


def test_form_matches_manual_calculation(tmp_path):
    m = _matches(tmp_path)
    out = add_form_features(m, window=5, min_periods=3)
    team = "Team C"
    played = []
    for _, r in out.iterrows():
        if team in (r["HomeTeam"], r["AwayTeam"]):
            is_home = r["HomeTeam"] == team
            gf, ga = (r["FTHG"], r["FTAG"]) if is_home else (r["FTAG"], r["FTHG"])
            got = r["home_gf_form"] if is_home else r["away_gf_form"]
            prev = played[-5:]
            if len(prev) >= 3:
                assert np.isclose(got, np.mean([p[0] for p in prev]))
            else:
                assert np.isnan(got)
            played.append((gf, ga))


def test_features_never_use_the_current_match(tmp_path):
    m = _matches(tmp_path)
    before = add_form_features(m)
    changed = m.copy()
    last = len(changed) - 1
    changed.loc[last, ["FTHG", "FTAG", "HS", "AS", "HST", "AST"]] = [9, 0, 40, 0, 20, 0]
    after = add_form_features(changed)
    cols = feature_columns(before)
    pd.testing.assert_frame_equal(before.loc[[last], cols], after.loc[[last], cols])


def test_baseline_runs_end_to_end(tmp_path):
    write_fake_raw_dir(tmp_path / "raw")
    out = run(tmp_path / "raw", tmp_path / "out", test_fraction=0.2)
    table = out["results"].set_index("model")
    assert {"Class frequencies", "Logistic Regression", "Bet365 odds"} <= set(table.index)
    preds = out["predictions"]
    assert np.allclose(preds[["P_A", "P_D", "P_H"]].sum(axis=1), 1, atol=0.01)
    assert (tmp_path / "out" / "test_predictions.csv").exists()
    assert out["n_train"] > out["n_test"] > 0
