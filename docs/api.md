# API reference (Sprint 2)

Base URL: `http://127.0.0.1:5000`. All bodies are JSON. Times are ISO 8601 (`2024-10-02T20:00:00`), dates are `YYYY-MM-DD`.
Errors return `{"error": "message"}` with status 400 (bad input) or 404.

## Children
| Method | Path | Notes |
|---|---|---|
| GET | `/children` | list all |
| POST | `/children` | `{"name","sex","date_of_birth"}`; sex is male/female/other |
| GET / PUT / DELETE | `/children/<id>` | PUT accepts any subset of fields; DELETE removes all their data |
| GET | `/children/<id>/summary` | everything one dashboard card needs |

Summary response:
```json
{
  "child": {"id": 1, "name": "Emma Smith", "sex": "female", "date_of_birth": "2025-12-08"},
  "age_months": 9,
  "last_sleep": {"start_time": "...", "end_time": "...", "duration_minutes": 95},
  "last_feed": {"fed_at": "...", "feed_type": "formula", "amount_ml": 150},
  "today": {"sleep_minutes": 600, "sleep_sessions": 2, "milk_ml": 450, "feeds": 6}
}
```

## Sleep: `/children/<id>/sleep`
| Method | Path | Notes |
|---|---|---|
| POST | `/sleep` | `{"start_time","end_time","notes"?}`; end must be after start |
| GET | `/sleep?days=7` | entries from the last N days (default 7) |
| DELETE | `/sleep/<entry_id>` | |
| GET | `/sleep/daily?days=7` | graph data: per day `total_minutes`, `total_hours`, `naps`, plus `average_daily_minutes`. Sleeps crossing midnight are split across days. A nap is a sleep starting 07:00-19:00. |

## Feeding: `/children/<id>/feeding`
| Method | Path | Notes |
|---|---|---|
| POST | `/feeding` | liquids: `{"fed_at","feed_type":"formula\|cow_milk\|breast_milk\|other_milk","amount_ml"}`; solids: `{"fed_at","feed_type":"solid","food_name","portion":"none\|some\|half\|most\|all"}` |
| GET | `/feeding?days=7` | entries from last N days |
| DELETE | `/feeding/<entry_id>` | |
| GET | `/feeding/daily?days=7` | per day `total_milk_ml`, `solid_meals`, `average_solid_intake` (0 to 1, null if no solids) |

Portion scores: none=0, some=0.25, half=0.5, most=0.75, all=1.

## Coming in Sprint 3
Nappy, medication, temperature, growth endpoints; medication plans; PDF daily report.
