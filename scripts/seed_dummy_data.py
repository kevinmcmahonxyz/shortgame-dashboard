"""
Generate 24 rounds of seed data calibrated to Grint averages.

Usage: python -m scripts.seed_dummy_data
"""

import random
from datetime import date, timedelta

from backend.constants import DISTANCES, DISTANCE_TO_FEET
from backend.storage.database import Hole, Putt, Round, get_session, init_db

# 1st putt make percentages by distance (from Grint data + interpolation)
# Tuned slightly lower at mid-range to hit ~32.8 PPR target
MAKE_PCT: dict[str, float] = {
    "Gimmie": 1.00,
    "3ft": 0.76,
    "4ft": 0.65,
    "5ft": 0.50,
    "6ft": 0.40,
    "7ft": 0.32,
    "8ft": 0.25,
    "10ft": 0.17,
    "15ft": 0.08,
    "20ft": 0.06,
    "25ft": 0.04,
    "30ft": 0.02,
    "40ft": 0.01,
    "50ft": 0.005,
    "50ft+": 0.002,
}

# 3-putt rates by distance (calibrated to Grint data, tuned for ~32.8 PPR)
# 3-putt rates by 1st putt distance (from Grint data at 30ft+, interpolated below)
THREE_PUTT_RATE: dict[str, float] = {
    "Gimmie": 0.0,
    "3ft": 0.0,
    "4ft": 0.0,
    "5ft": 0.0,
    "6ft": 0.0,
    "7ft": 0.0,
    "8ft": 0.01,
    "10ft": 0.02,
    "15ft": 0.03,
    "20ft": 0.03,
    "25ft": 0.03,
    "30ft": 0.04,   # Grint: 3%
    "40ft": 0.52,   # Grint: 50%
    "50ft": 0.55,   # Grint: 42% (bumped to ensure monotonic with variance)
    "50ft+": 0.70,  # Grint: 66%
}

# Distribution of 1st putt distances for GIR holes
GIR_FIRST_PUTT_WEIGHTS: dict[str, float] = {
    "Gimmie": 0.01,
    "3ft": 0.02,
    "4ft": 0.03,
    "5ft": 0.04,
    "6ft": 0.05,
    "7ft": 0.06,
    "8ft": 0.07,
    "10ft": 0.10,
    "15ft": 0.14,
    "20ft": 0.15,
    "25ft": 0.11,
    "30ft": 0.09,
    "40ft": 0.07,
    "50ft": 0.05,
    "50ft+": 0.03,
}

# Distribution of 1st putt distances for non-GIR holes
# Average approach ~8ft target to get average around 8-9ft
NON_GIR_FIRST_PUTT_WEIGHTS: dict[str, float] = {
    "Gimmie": 0.03,
    "3ft": 0.08,
    "4ft": 0.09,
    "5ft": 0.10,
    "6ft": 0.10,
    "7ft": 0.10,
    "8ft": 0.10,
    "10ft": 0.12,
    "15ft": 0.10,
    "20ft": 0.08,
    "25ft": 0.04,
    "30ft": 0.03,
    "40ft": 0.02,
    "50ft": 0.01,
    "50ft+": 0.00,
}

# After missing, leave distance distribution
# Realistic: most misses leave 2-5ft, longer putts leave a bit longer
# but rarely beyond 6-7ft unless it's a really bad miss (3-putt territory)
LEAVE_DISTANCES: dict[str, list[tuple[str, float]]] = {
    "Gimmie": [("Gimmie", 1.0)],  # shouldn't happen (gimmies are auto-made)
    "3ft": [("Gimmie", 0.30), ("3ft", 0.50), ("4ft", 0.20)],
    "4ft": [("Gimmie", 0.20), ("3ft", 0.50), ("4ft", 0.25), ("5ft", 0.05)],
    "5ft": [("Gimmie", 0.15), ("3ft", 0.45), ("4ft", 0.25), ("5ft", 0.10), ("6ft", 0.05)],
    "6ft": [("Gimmie", 0.10), ("3ft", 0.40), ("4ft", 0.30), ("5ft", 0.12), ("6ft", 0.08)],
    "7ft": [("Gimmie", 0.08), ("3ft", 0.35), ("4ft", 0.30), ("5ft", 0.15), ("6ft", 0.08), ("7ft", 0.04)],
    "8ft": [("Gimmie", 0.06), ("3ft", 0.30), ("4ft", 0.30), ("5ft", 0.18), ("6ft", 0.10), ("7ft", 0.06)],
    "10ft": [("Gimmie", 0.04), ("3ft", 0.25), ("4ft", 0.30), ("5ft", 0.20), ("6ft", 0.12), ("7ft", 0.06), ("8ft", 0.03)],
    "15ft": [("Gimmie", 0.03), ("3ft", 0.20), ("4ft", 0.28), ("5ft", 0.22), ("6ft", 0.14), ("7ft", 0.07), ("8ft", 0.04), ("10ft", 0.02)],
    "20ft": [("3ft", 0.15), ("4ft", 0.25), ("5ft", 0.25), ("6ft", 0.15), ("7ft", 0.10), ("8ft", 0.05), ("10ft", 0.05)],
    "25ft": [("3ft", 0.12), ("4ft", 0.20), ("5ft", 0.25), ("6ft", 0.18), ("7ft", 0.12), ("8ft", 0.07), ("10ft", 0.06)],
    "30ft": [("3ft", 0.08), ("4ft", 0.15), ("5ft", 0.20), ("6ft", 0.18), ("7ft", 0.13), ("8ft", 0.10), ("10ft", 0.08), ("15ft", 0.04), ("20ft", 0.02), ("25ft", 0.02)],
    "40ft": [("3ft", 0.05), ("4ft", 0.10), ("5ft", 0.15), ("6ft", 0.17), ("7ft", 0.14), ("8ft", 0.12), ("10ft", 0.10), ("15ft", 0.07), ("20ft", 0.04), ("25ft", 0.03), ("30ft", 0.02), ("40ft", 0.01)],
    "50ft": [("3ft", 0.03), ("4ft", 0.08), ("5ft", 0.12), ("6ft", 0.15), ("7ft", 0.15), ("8ft", 0.12), ("10ft", 0.10), ("15ft", 0.08), ("20ft", 0.06), ("25ft", 0.04), ("30ft", 0.03), ("40ft", 0.02), ("50ft", 0.02)],
    "50ft+": [("3ft", 0.02), ("4ft", 0.06), ("5ft", 0.10), ("6ft", 0.13), ("7ft", 0.14), ("8ft", 0.12), ("10ft", 0.12), ("15ft", 0.09), ("20ft", 0.07), ("25ft", 0.05), ("30ft", 0.04), ("40ft", 0.03), ("50ft", 0.02), ("50ft+", 0.01)],
}


def _pick_weighted(items: dict[str, float]) -> str:
    """Pick a random item based on weights."""
    labels = list(items.keys())
    weights = list(items.values())
    return random.choices(labels, weights=weights, k=1)[0]


def _pick_leave(first_putt_dist: str) -> str:
    """Pick a leave distance after missing a putt."""
    leaves = LEAVE_DISTANCES[first_putt_dist]
    labels = [d for d, _ in leaves]
    weights = [w for _, w in leaves]
    return random.choices(labels, weights=weights, k=1)[0]


def simulate_hole(gir: bool) -> tuple[bool, list[str]]:
    """
    Simulate putting on a single hole.
    Returns (gir, list_of_putt_distances).
    """
    weights = GIR_FIRST_PUTT_WEIGHTS if gir else NON_GIR_FIRST_PUTT_WEIGHTS
    first_dist = _pick_weighted(weights)
    putts = [first_dist]

    # Determine if 1st putt is made
    if first_dist == "Gimmie" or random.random() < MAKE_PCT[first_dist]:
        return gir, putts  # 1 putt

    # Determine if 3-putt
    is_three_putt = random.random() < THREE_PUTT_RATE.get(first_dist, 0)

    # 2nd putt distance
    second_dist = _pick_leave(first_dist)
    putts.append(second_dist)

    if not is_three_putt:
        return gir, putts  # 2 putts

    # 3rd putt - short leave
    third_dist = _pick_leave(second_dist)
    putts.append(third_dist)
    return gir, putts  # 3 putts


def generate_round(round_date: date, round_num: int) -> None:
    """Generate a single seed round."""
    gir_rate = 0.47  # 47% GIR = ~8.5 greens per round

    with get_session() as session:
        round_obj = Round(
            telegram_user_id="seed",
            date=round_date,
            course_name=f"Seed Round {round_num}",
            is_seed=True,
        )
        session.add(round_obj)
        session.commit()
        session.refresh(round_obj)

        for hole_num in range(1, 19):
            gir = random.random() < gir_rate
            gir_result, putt_distances = simulate_hole(gir)

            hole = Hole(
                round_id=round_obj.id,
                hole_number=hole_num,
                gir=gir_result,
                putts_taken=len(putt_distances),
            )
            session.add(hole)
            session.commit()
            session.refresh(hole)

            for i, dist in enumerate(putt_distances):
                putt = Putt(
                    hole_id=hole.id,
                    putt_number=i + 1,
                    distance=dist,
                )
                session.add(putt)

            session.commit()


def seed(num_rounds: int = 24) -> None:
    """Generate seed rounds spread across the past 6 months."""
    init_db()

    # Check if seed data already exists
    with get_session() as session:
        from sqlmodel import select
        existing = session.exec(
            select(Round).where(Round.is_seed == True)
        ).all()
        if existing:
            print(f"Seed data already exists ({len(existing)} rounds). Skipping.")
            return

    today = date.today()
    days_span = 180  # 6 months

    random.seed(42)  # Reproducible

    for i in range(num_rounds):
        days_ago = int(days_span * (1 - i / (num_rounds - 1)))
        round_date = today - timedelta(days=days_ago)
        generate_round(round_date, i + 1)
        print(f"  Generated round {i + 1}: {round_date}")

    # Print summary
    with get_session() as session:
        from sqlmodel import select, func
        rounds = session.exec(select(Round).where(Round.is_seed == True)).all()
        total_putts = 0
        for r in rounds:
            holes = session.exec(select(Hole).where(Hole.round_id == r.id)).all()
            for h in holes:
                putts = session.exec(select(Putt).where(Putt.hole_id == h.id)).all()
                total_putts += len(putts)

        avg_putts = total_putts / len(rounds) if rounds else 0
        print(f"\nSeeded {len(rounds)} rounds")
        print(f"Average putts per round: {avg_putts:.1f}")


if __name__ == "__main__":
    seed()
