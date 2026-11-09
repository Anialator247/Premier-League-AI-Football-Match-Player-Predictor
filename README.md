# Child Health and Well-Being Tracker

Backend: Python, Flask, SQLite (via Flask-SQLAlchemy). Frontend: dashboard-style UI (one card per child).

## Run the backend

```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python seed.py                 # optional: sample data for 2 children
python run.py                  # API at http://127.0.0.1:5000
```

Check it works: open http://127.0.0.1:5000/children

## Run the tests

```
cd backend
python -m pytest
```

## Project layout

```
backend/
  run.py            start the server
  seed.py           sample data (wipes the DB!)
  app/
    __init__.py     app factory
    models.py       database tables
    routes/         children.py, sleep.py, feeding.py
  tests/            automated tests
docs/api.md         endpoint reference for the frontend team
```

## Team rules
- Never commit directly to `main`: use a feature branch (`feature/short-name`) and a merge request.
- Pull before you start work, push when you finish.
- Store units in the DB as ml, kg, cm, Celsius. Convert only when displaying.
