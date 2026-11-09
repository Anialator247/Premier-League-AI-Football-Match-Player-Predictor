# Premier League Analytics

A machine learning project that predicts Premier League match outcomes and, over time, will analyse teams and players. It starts with an honest baseline: how well can a simple model beat the class frequencies, and how close does it get to the bookmakers?

**Status: early stage.** Match outcome prediction with a Logistic Regression baseline is working. Everything else is on the roadmap below.

## What works so far

- Downloads Premier League results from [football-data.co.uk](https://www.football-data.co.uk/) and loads them into one clean table
- Builds rolling "form" features for each team (points, goals for and against, shots, shots on target over the previous 5 matches)
- Predicts home win, draw or away win with a probability for each
- Evaluates on a **chronological split** (train on the past, test on the most recent matches) so the model never sees the future
- Compares against two baselines: the class frequencies and Bet365 odds with the bookmaker margin removed
- Saves every test prediction next to the actual result in `outputs/test_predictions.csv`
- Tests that check the features cannot leak the current match's result

## Quick start

```bash
git clone https://github.com/Anialator247/premier-league-analytics
cd premier-league-analytics
pip install -r requirements.txt

python -m pl_analytics.download --start 2015 --end 2025   # fetch season CSVs into data/raw
python -m pl_analytics.train_baseline                      # train and evaluate
pytest                                                     # run the tests
```

## Results

Evaluated on the most recent 20% of matches (822 test matches, 2024-04-13 to 2026-05-24), after training on 3,286 earlier matches:

| Model | Accuracy | Log loss |
|---|---:|---:|
| Class frequencies | 0.421 | 1.079 |
| Logistic Regression | 0.495 | 1.032 |
| Bet365 odds | 0.529 | 0.983 |

Accuracy alone is a weak measure for three-way outcomes, so the table reports log loss too (lower is better), because it scores the probabilities and not just the top pick.

## Design decisions

- **No data leakage.** Features use `shift(1)` before the rolling mean, so a match's features only come from earlier matches. A test changes the final match's score and checks that its own features do not move.
- **Time-based split, not random.** A random split would let the model train on matches played after the ones it is tested on.
- **Bookmaker odds as a benchmark, not a feature.** Odds already contain a lot of information, so using them as inputs would hide whether the model learned anything. They are kept for comparison only.

## Roadmap

- [x] Data download and loading
- [x] Rolling form features with leakage tests
- [x] Logistic Regression baseline with probabilities and bookmaker comparison
- [ ] Random Forest for match outcomes
- [ ] Probability calibration plot (are 60% predictions right about 60% of the time?)
- [ ] XGBoost, if it improves on Random Forest
- [ ] Team analysis: over and underperformers, home versus away splits
- [ ] Player performance prediction and similar-player comparison
- [ ] K-Means clustering of players by playing style
- [ ] Streamlit dashboard

## Data notes

- Match data comes from football-data.co.uk, which also provides shots and Bet365 odds.
- StatsBomb Open Data only covers selected competitions and seasons, so check what Premier League coverage exists before building the player models on it.

## Project structure

```
pl_analytics/
  data.py            download and load season CSVs
  features.py        rolling form features
  evaluate.py        metrics and bookmaker baseline
  train_baseline.py  Logistic Regression baseline
tests/               pytest tests using synthetic data
```
