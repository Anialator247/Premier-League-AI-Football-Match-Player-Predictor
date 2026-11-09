"""Fills the database with sample data so the frontend can test graphs.

Run from the backend folder:  python seed.py
WARNING: this wipes the existing database first.
"""
import random
from datetime import date, datetime, time, timedelta

from app import create_app
from app.extensions import db
from app.models import Child, FeedingEntry, SleepEntry

random.seed(42)
app = create_app()


def at(day, hh, mm=0):
    return datetime.combine(day, time(hh, mm))


with app.app_context():
    db.drop_all()
    db.create_all()

    today = date.today()
    emma = Child(name="Emma Smith", sex="female", date_of_birth=today - timedelta(days=300))
    noah = Child(name="Noah Patel", sex="male", date_of_birth=today - timedelta(days=700))
    db.session.add_all([emma, noah])
    db.session.commit()

    for i in range(30, -1, -1):
        day = today - timedelta(days=i)
        for child in (emma, noah):
            # night sleep crossing midnight
            night_start = at(day, 19, 0) + timedelta(minutes=30 + random.randint(0, 40))
            db.session.add(SleepEntry(child_id=child.id, start_time=night_start,
                                      end_time=night_start + timedelta(hours=10, minutes=random.randint(-45, 45))))
            # afternoon nap
            nap_start = at(day, 12, random.randint(0, 45))
            db.session.add(SleepEntry(child_id=child.id, start_time=nap_start,
                                      end_time=nap_start + timedelta(minutes=random.randint(60, 120))))
            # milk
            for hh in (7, 15, 19):
                db.session.add(FeedingEntry(child_id=child.id, fed_at=at(day, hh), feed_type="formula",
                                            amount_ml=random.choice([120, 150, 180, 210])))
            # solids
            for hh, food in ((8, "porridge"), (12, random.choice(["pasta", "jacket potato", "risotto"])),
                             (17, random.choice(["chicken curry with rice", "chilli con carne"]))):
                db.session.add(FeedingEntry(child_id=child.id, fed_at=at(day, hh, 30), feed_type="solid",
                                            food_name=food,
                                            portion=random.choice(["some", "half", "most", "all"])))
    db.session.commit()
    print("Seeded 2 children with 31 days of sleep and feeding data.")
