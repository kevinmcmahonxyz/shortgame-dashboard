"""
Load seed data from the JSON fixture into the database.

Usage: python -m scripts.seed_dummy_data
"""

import json
from datetime import date
from pathlib import Path

from sqlmodel import select

from backend.storage.database import Hole, Putt, Round, get_session, init_db

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"


def seed() -> None:
    """Load seed rounds from the JSON fixture file."""
    init_db()

    # Check if seed data already exists
    with get_session() as session:
        existing = session.exec(
            select(Round).where(Round.is_seed == True)
        ).all()
        if existing:
            print(f"Seed data already exists ({len(existing)} rounds). Skipping.")
            return

    with open(FIXTURE_PATH) as f:
        data = json.load(f)

    with get_session() as session:
        for round_data in data["rounds"]:
            round_obj = Round(
                telegram_user_id="seed",
                date=date.fromisoformat(round_data["date"]),
                course_name=round_data["course_name"],
                is_seed=True,
            )
            session.add(round_obj)
            session.commit()
            session.refresh(round_obj)

            for hole_data in round_data["holes"]:
                hole = Hole(
                    round_id=round_obj.id,
                    hole_number=hole_data["hole_number"],
                    gir=hole_data["gir"],
                    putts_taken=hole_data["putts_taken"],
                )
                session.add(hole)
                session.commit()
                session.refresh(hole)

                for putt_data in hole_data["putts"]:
                    putt = Putt(
                        hole_id=hole.id,
                        putt_number=putt_data["putt_number"],
                        distance=putt_data["distance"],
                    )
                    session.add(putt)

            session.commit()

    print(f"Loaded {len(data['rounds'])} seed rounds from {FIXTURE_PATH.name}")


if __name__ == "__main__":
    seed()
