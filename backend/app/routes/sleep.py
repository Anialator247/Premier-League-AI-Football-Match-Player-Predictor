from collections import defaultdict
from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Child, SleepEntry
from ..utils import date_range_from_args, error, parse_datetime

bp = Blueprint("sleep", __name__, url_prefix="/children/<int:child_id>/sleep")


@bp.post("")
def add_sleep(child_id):
    db.get_or_404(Child, child_id)
    data = request.get_json(silent=True) or {}
    try:
        start = parse_datetime(data.get("start_time"), "start_time")
        end = parse_datetime(data.get("end_time"), "end_time")
    except ValueError as e:
        return error(str(e))
    if end <= start:
        return error("'end_time' must be after 'start_time'")
    if end - start > timedelta(hours=24):
        return error("A single sleep cannot be longer than 24 hours")

    entry = SleepEntry(child_id=child_id, start_time=start, end_time=end,
                       notes=data.get("notes"))
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@bp.get("")
def list_sleep(child_id):
    """Optional filter: ?days=7 (default 7)."""
    db.get_or_404(Child, child_id)
    try:
        start, end = date_range_from_args(request.args)
    except ValueError as e:
        return error(str(e))
    entries = (SleepEntry.query.filter_by(child_id=child_id)
               .filter(SleepEntry.start_time >= start, SleepEntry.start_time < end)
               .order_by(SleepEntry.start_time).all())
    return jsonify([e.to_dict() for e in entries])


@bp.delete("/<int:entry_id>")
def delete_sleep(child_id, entry_id):
    entry = SleepEntry.query.filter_by(id=entry_id, child_id=child_id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return "", 204


@bp.get("/daily")
def daily_sleep(child_id):
    """Total sleep minutes and number of sleeps per day (for line/bar graphs).

    A sleep that crosses midnight is split so each day gets its own share.
    A 'nap' is any sleep that starts between 07:00 and 19:00.
    """
    db.get_or_404(Child, child_id)
    try:
        start, end = date_range_from_args(request.args)
    except ValueError as e:
        return error(str(e))

    entries = (SleepEntry.query.filter_by(child_id=child_id)
               .filter(SleepEntry.end_time > start, SleepEntry.start_time < end).all())

    minutes = defaultdict(float)
    naps = defaultdict(int)
    for e in entries:
        if time(7) <= e.start_time.time() < time(19):
            naps[e.start_time.date()] += 1
        cursor = e.start_time
        while cursor < e.end_time:
            midnight = datetime.combine(cursor.date() + timedelta(days=1), time.min)
            chunk_end = min(e.end_time, midnight)
            minutes[cursor.date()] += (chunk_end - cursor).total_seconds() / 60
            cursor = chunk_end

    days = []
    day = start.date()
    while day < end.date():
        days.append({
            "date": day.isoformat(),
            "total_minutes": round(minutes.get(day, 0)),
            "total_hours": round(minutes.get(day, 0) / 60, 2),
            "naps": naps.get(day, 0),
        })
        day += timedelta(days=1)

    total = sum(d["total_minutes"] for d in days)
    return jsonify({
        "days": days,
        "average_daily_minutes": round(total / len(days)) if days else 0,
    })
