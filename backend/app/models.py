"""Database models.

Design rules (agreed for the whole team):
- Every record table has a child_id foreign key, so switching child
  filters all data automatically.
- Store units consistently: ml, kg, cm, Celsius. Convert on display only.
- Store times as full datetimes so sleeps crossing midnight work.
"""
from datetime import datetime

from .extensions import db

# Scale from the brief: None=0, Some=0.25, Half=0.5, Most=0.75, All=1
PORTION_SCORES = {"none": 0.0, "some": 0.25, "half": 0.5, "most": 0.75, "all": 1.0}
FEED_TYPES_LIQUID = {"formula", "cow_milk", "breast_milk", "other_milk"}
FEED_TYPES = FEED_TYPES_LIQUID | {"solid"}


class Child(db.Model):
    __tablename__ = "children"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)  # male / female / other
    date_of_birth = db.Column(db.Date, nullable=False)

    sleep_entries = db.relationship("SleepEntry", backref="child", cascade="all, delete-orphan")
    feeding_entries = db.relationship("FeedingEntry", backref="child", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "sex": self.sex,
            "date_of_birth": self.date_of_birth.isoformat(),
        }


class SleepEntry(db.Model):
    __tablename__ = "sleep_entries"
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.String(500))

    @property
    def duration_minutes(self):
        return int((self.end_time - self.start_time).total_seconds() // 60)

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
        }


class FeedingEntry(db.Model):
    __tablename__ = "feeding_entries"
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False, index=True)
    fed_at = db.Column(db.DateTime, nullable=False)
    feed_type = db.Column(db.String(20), nullable=False)
    amount_ml = db.Column(db.Float)          # liquids only
    food_name = db.Column(db.String(100))    # solids only, e.g. "pasta"
    portion = db.Column(db.String(10))       # solids only: none/some/half/most/all
    notes = db.Column(db.String(500))

    @property
    def portion_score(self):
        return PORTION_SCORES.get(self.portion) if self.portion else None

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "fed_at": self.fed_at.isoformat(),
            "feed_type": self.feed_type,
            "amount_ml": self.amount_ml,
            "food_name": self.food_name,
            "portion": self.portion,
            "portion_score": self.portion_score,
            "notes": self.notes,
        }
