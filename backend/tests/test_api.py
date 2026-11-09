from datetime import date, datetime, timedelta

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.test_client() as c:
        yield c


def make_child(client, name="Emma"):
    r = client.post("/children", json={"name": name, "sex": "female", "date_of_birth": "2024-01-15"})
    assert r.status_code == 201
    return r.get_json()["id"]


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_child_crud(client):
    cid = make_child(client)
    assert client.get(f"/children/{cid}").get_json()["name"] == "Emma"
    assert client.put(f"/children/{cid}", json={"name": "Emmy"}).get_json()["name"] == "Emmy"
    assert len(client.get("/children").get_json()) == 1
    assert client.delete(f"/children/{cid}").status_code == 204
    assert client.get(f"/children/{cid}").status_code == 404


@pytest.mark.parametrize("payload", [
    {"sex": "female", "date_of_birth": "2024-01-15"},
    {"name": "A", "sex": "robot", "date_of_birth": "2024-01-15"},
    {"name": "A", "sex": "male", "date_of_birth": "not-a-date"},
    {"name": "A", "sex": "male", "date_of_birth": "2999-01-01"},
])
def test_child_validation(client, payload):
    assert client.post("/children", json=payload).status_code == 400


def test_sleep_validation(client):
    cid = make_child(client)
    bad = client.post(f"/children/{cid}/sleep",
                      json={"start_time": "2024-10-02T20:00:00", "end_time": "2024-10-02T19:00:00"})
    assert bad.status_code == 400
    assert client.post("/children/999/sleep", json={}).status_code == 404


def test_sleep_crossing_midnight_is_split(client):
    cid = make_child(client)
    today = date.today()
    start = datetime.combine(today - timedelta(days=1), datetime.min.time()).replace(hour=22)
    end = start + timedelta(hours=8)  # 22:00 -> 06:00
    r = client.post(f"/children/{cid}/sleep",
                    json={"start_time": start.isoformat(), "end_time": end.isoformat()})
    assert r.get_json()["duration_minutes"] == 480
    days = {d["date"]: d for d in client.get(f"/children/{cid}/sleep/daily?days=3").get_json()["days"]}
    assert days[(today - timedelta(days=1)).isoformat()]["total_minutes"] == 120
    assert days[today.isoformat()]["total_minutes"] == 360


def test_feeding_milk_and_solids(client):
    cid = make_child(client)
    today = date.today().isoformat()
    assert client.post(f"/children/{cid}/feeding", json={
        "fed_at": f"{today}T08:00:00", "feed_type": "formula", "amount_ml": 150}).status_code == 201
    for t, p in (("12:00:00", "half"), ("18:00:00", "all")):
        assert client.post(f"/children/{cid}/feeding", json={
            "fed_at": f"{today}T{t}", "feed_type": "solid", "food_name": "pasta", "portion": p}).status_code == 201
    today_row = client.get(f"/children/{cid}/feeding/daily?days=1").get_json()["days"][0]
    assert today_row["total_milk_ml"] == 150
    assert today_row["average_solid_intake"] == 0.75


def test_feeding_validation(client):
    cid = make_child(client)
    base = {"fed_at": "2024-10-02T08:00:00"}
    assert client.post(f"/children/{cid}/feeding", json={**base, "feed_type": "formula"}).status_code == 400
    assert client.post(f"/children/{cid}/feeding", json={**base, "feed_type": "solid", "food_name": "x", "portion": "lots"}).status_code == 400
    assert client.post(f"/children/{cid}/feeding", json={**base, "feed_type": "lava"}).status_code == 400


def test_data_is_separate_per_child(client):
    a, b = make_child(client, "A"), make_child(client, "B")
    now = datetime.now()
    client.post(f"/children/{a}/sleep", json={
        "start_time": (now - timedelta(hours=2)).isoformat(), "end_time": (now - timedelta(hours=1)).isoformat()})
    assert len(client.get(f"/children/{a}/sleep").get_json()) == 1
    assert client.get(f"/children/{b}/sleep").get_json() == []


def test_summary(client):
    cid = make_child(client)
    s = client.get(f"/children/{cid}/summary").get_json()
    assert s["last_sleep"] is None and s["today"]["feeds"] == 0
