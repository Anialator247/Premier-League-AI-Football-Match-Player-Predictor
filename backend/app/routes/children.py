from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..extensions import db
from ..models import Child, FeedingEntry, SleepEntry
from ..utils import error, parse_date

bp = Blueprint("children", __name__, url_prefix="/children")
VALID_SEX = {"male", "female", "other"}


def _validate(data, partial=False):
    """Returns (clean_dict, error_message)."""
    clean = {}
    if "name" in data or not partial:
        name = (data.get("name") or "").strip()
        if not name:
            return None, "'name' is required"
        clean["name"] = name
    if "sex" in data or not partial:
        sex = str(data.get("sex", "")).lower()
        if sex not in VALID_SEX:
            return None, "'sex' must be one of: male, female, other"
        clean["sex"] = sex
    if "date_of_birth" in data or not partial:
        try:
            dob = parse_date(data.get("date_of_birth"), "date_of_birth")
        except ValueError as e:
            return None, str(e)
        if dob > date.today():
            return None, "'date_of_birth' cannot be in the future"
        clean["date_of_birth"] = dob
    return clean, None


@bp.get("")
def list_children():
    return jsonify([c.to_dict() for c in Child.query.order_by(Child.name).all()])


@bp.post("")
def create_child():
    clean, err = _validate(request.get_json(silent=True) or {})
    if err:
        return error(err)
    child = Child(**clean)
    db.session.add(child)
    db.session.commit()
    return jsonify(child.to_dict()), 201


@bp.get("/<int:child_id>")
def get_child(child_id):
    return jsonify(db.get_or_404(Child, child_id).to_dict())


@bp.put("/<int:child_id>")
def update_child(child_id):
    child = db.get_or_404(Child, child_id)
    clean, err = _validate(request.get_json(silent=True) or {}, partial=True)
    if err:
        return error(err)
    for k, v in clean.items():
        setattr(child, k, v)
    db.session.commit()
    return jsonify(child.to_dict())


@bp.delete("/<int:child_id>")
def delete_child(child_id):
    child = db.get_or_404(Child, child_id)
    db.session.delete(child)
    db.session.commit()
    return "", 204


@bp.get("/<int:child_id>/summary")
def summary(child_id):
    """One call that returns everything a dashboard card needs."""
    child = db.get_or_404(Child, child_id)
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    last_sleep = (SleepEntry.query.filter_by(child_id=child_id)
                  .order_by(SleepEntry.end_time.desc()).first())
    last_feed = (FeedingEntry.query.filter_by(child_id=child_id)
                 .order_by(FeedingEntry.fed_at.desc()).first())

    sleeps_today = (SleepEntry.query.filter_by(child_id=child_id)
                    .filter(SleepEntry.start_time >= today_start,
                            SleepEntry.start_time < today_end).all())
    milk_today = (db.session.query(func.coalesce(func.sum(FeedingEntry.amount_ml), 0))
                  .filter(FeedingEntry.child_id == child_id,
                          FeedingEntry.fed_at >= today_start,
                          FeedingEntry.fed_at < today_end).scalar())
    feeds_today = (FeedingEntry.query.filter_by(child_id=child_id)
                   .filter(FeedingEntry.fed_at >= today_start,
                           FeedingEntry.fed_at < today_end).count())

    age_days = (date.today() - child.date_of_birth).days
    return jsonify({
        "child": child.to_dict(),
        "age_months": int(age_days // 30.4375),
        "last_sleep": last_sleep.to_dict() if last_sleep else None,
        "last_feed": last_feed.to_dict() if last_feed else None,
        "today": {
            "sleep_minutes": sum(s.duration_minutes for s in sleeps_today),
            "sleep_sessions": len(sleeps_today),
            "milk_ml": float(milk_today),
            "feeds": feeds_today,
        },
    })
