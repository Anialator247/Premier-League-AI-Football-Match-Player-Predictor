from datetime import date, datetime, timedelta

from flask import jsonify


def error(message, status=400):
    return jsonify(error=message), status


def parse_datetime(value, field):
    """Parse an ISO 8601 string like 2024-10-02T12:00:00. Raises ValueError."""
    if not isinstance(value, str):
        raise ValueError(f"'{field}' is required (ISO format, e.g. 2024-10-02T12:00:00)")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"'{field}' must be ISO format, e.g. 2024-10-02T12:00:00")


def parse_date(value, field):
    if not isinstance(value, str):
        raise ValueError(f"'{field}' is required (format YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"'{field}' must be in format YYYY-MM-DD")


def date_range_from_args(args, default_days=7):
    """Reads ?days=N (default 7) and returns (start_datetime, end_datetime)."""
    try:
        days = int(args.get("days", default_days))
    except ValueError:
        raise ValueError("'days' must be a whole number")
    if not 1 <= days <= 366:
        raise ValueError("'days' must be between 1 and 366")
    end = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    start = end - timedelta(days=days)
    return start, end
