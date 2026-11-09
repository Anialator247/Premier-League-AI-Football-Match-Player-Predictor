from collections import defaultdict
from datetime import timedelta

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import FEED_TYPES, FEED_TYPES_LIQUID, PORTION_SCORES, Child, FeedingEntry
from ..utils import date_range_from_args, error, parse_datetime

bp = Blueprint("feeding", __name__, url_prefix="/children/<int:child_id>/feeding")


@bp.post("")
def add_feeding(child_id):
    db.get_or_404(Child, child_id)
    data = request.get_json(silent=True) or {}
    try:
        fed_at = parse_datetime(data.get("fed_at"), "fed_at")
    except ValueError as e:
        return error(str(e))

    feed_type = str(data.get("feed_type", "")).lower()
    if feed_type not in FEED_TYPES:
        return error(f"'feed_type' must be one of: {', '.join(sorted(FEED_TYPES))}")

    entry = FeedingEntry(child_id=child_id, fed_at=fed_at, feed_type=feed_type,
                         notes=data.get("notes"))

    if feed_type in FEED_TYPES_LIQUID:
        amount = data.get("amount_ml")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            return error("'amount_ml' must be a positive number for liquid feeds")
        entry.amount_ml = float(amount)
    else:
        food = (data.get("food_name") or "").strip()
        portion = str(data.get("portion", "")).lower()
        if not food:
            return error("'food_name' is required for solids")
        if portion not in PORTION_SCORES:
            return error("'portion' must be one of: none, some, half, most, all")
        entry.food_name = food
        entry.portion = portion

    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@bp.get("")
def list_feeding(child_id):
    """Optional filter: ?days=7 (default 7)."""
    db.get_or_404(Child, child_id)
    try:
        start, end = date_range_from_args(request.args)
    except ValueError as e:
        return error(str(e))
    entries = (FeedingEntry.query.filter_by(child_id=child_id)
               .filter(FeedingEntry.fed_at >= start, FeedingEntry.fed_at < end)
               .order_by(FeedingEntry.fed_at).all())
    return jsonify([e.to_dict() for e in entries])


@bp.delete("/<int:entry_id>")
def delete_feeding(child_id, entry_id):
    entry = FeedingEntry.query.filter_by(id=entry_id, child_id=child_id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return "", 204


@bp.get("/daily")
def daily_feeding(child_id):
    """Per day: total milk (ml) and average solid intake (0 to 1)."""
    db.get_or_404(Child, child_id)
    try:
        start, end = date_range_from_args(request.args)
    except ValueError as e:
        return error(str(e))

    entries = (FeedingEntry.query.filter_by(child_id=child_id)
               .filter(FeedingEntry.fed_at >= start, FeedingEntry.fed_at < end).all())

    milk = defaultdict(float)
    solids = defaultdict(list)
    for e in entries:
        d = e.fed_at.date()
        if e.amount_ml:
            milk[d] += e.amount_ml
        if e.portion_score is not None:
            solids[d].append(e.portion_score)

    days = []
    day = start.date()
    while day < end.date():
        scores = solids.get(day, [])
        days.append({
            "date": day.isoformat(),
            "total_milk_ml": round(milk.get(day, 0), 1),
            "solid_meals": len(scores),
            "average_solid_intake": round(sum(scores) / len(scores), 2) if scores else None,
        })
        day += timedelta(days=1)
    return jsonify({"days": days})
