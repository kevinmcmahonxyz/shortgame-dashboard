from collections import defaultdict

from sqlmodel import select

from backend.constants import DISTANCES, DISTANCE_TO_FEET, GOALS, SG_BASELINE
from backend.storage.database import Hole, Putt, Round, get_session


def _feet_to_display(feet: float) -> str:
    """Convert feet (float) to ft'in\" display string."""
    ft = int(feet)
    inches = round((feet - ft) * 12)
    if inches == 12:
        ft += 1
        inches = 0
    return f"{ft}'{inches}\""


def compute_stats() -> dict:
    """Compute all dashboard statistics from the database."""
    with get_session() as session:
        rounds = session.exec(select(Round)).all()
        if not rounds:
            return _empty_stats()

        round_ids = [r.id for r in rounds]
        holes = session.exec(select(Hole).where(Hole.round_id.in_(round_ids))).all()
        hole_ids = [h.id for h in holes]
        putts = session.exec(select(Putt).where(Putt.hole_id.in_(hole_ids))).all()

    # Build lookup structures
    holes_by_round: dict[int, list[Hole]] = defaultdict(list)
    for h in holes:
        holes_by_round[h.round_id].append(h)

    # Filter to complete rounds only (18 holes)
    rounds = [r for r in rounds if len(holes_by_round[r.id]) == 18]
    if not rounds:
        return _empty_stats()

    # Rebuild hole list from complete rounds only
    complete_round_ids = {r.id for r in rounds}
    holes = [h for h in holes if h.round_id in complete_round_ids]
    hole_ids = [h.id for h in holes]

    putts_by_hole: dict[int, list[Putt]] = defaultdict(list)
    for p in putts:
        if p.hole_id in set(hole_ids):
            putts_by_hole[p.hole_id].append(p)

    # --- Putts Per Round ---
    round_putt_counts = []
    for r in rounds:
        total = sum(h.putts_taken for h in holes_by_round[r.id])
        round_putt_counts.append(total)
    putts_per_round = sum(round_putt_counts) / len(round_putt_counts) if round_putt_counts else 0

    # --- Up & Down % (1-putt rate on non-GIR holes) ---
    non_gir_holes = [h for h in holes if not h.gir]
    non_gir_one_putts = sum(1 for h in non_gir_holes if h.putts_taken == 1)
    up_and_down_pct = (non_gir_one_putts / len(non_gir_holes) * 100) if non_gir_holes else 0

    # --- Non-GIR Approach Distance ---
    non_gir_approach_distances = []
    for h in non_gir_holes:
        hole_putts = sorted(putts_by_hole[h.id], key=lambda p: p.putt_number)
        if hole_putts:
            first_dist = hole_putts[0].distance
            if first_dist in DISTANCE_TO_FEET:
                non_gir_approach_distances.append(DISTANCE_TO_FEET[first_dist])
    non_gir_approach_avg = (
        sum(non_gir_approach_distances) / len(non_gir_approach_distances)
        if non_gir_approach_distances
        else 0
    )

    # --- GIR Approach Distance ---
    gir_holes = [h for h in holes if h.gir]
    gir_approach_distances = []
    for h in gir_holes:
        hole_putts = sorted(putts_by_hole[h.id], key=lambda p: p.putt_number)
        if hole_putts:
            first_dist = hole_putts[0].distance
            if first_dist in DISTANCE_TO_FEET:
                gir_approach_distances.append(DISTANCE_TO_FEET[first_dist])
    gir_approach_avg = (
        sum(gir_approach_distances) / len(gir_approach_distances)
        if gir_approach_distances
        else 0
    )

    # --- SG:Putting ---
    sg_per_round = []
    for r in rounds:
        sg_round = 0.0
        for h in holes_by_round[r.id]:
            hole_putts = sorted(putts_by_hole[h.id], key=lambda p: p.putt_number)
            if hole_putts:
                first_dist = hole_putts[0].distance
                expected = SG_BASELINE.get(first_dist, 2.0)
                actual = h.putts_taken
                sg_round += expected - actual
        sg_per_round.append(sg_round)
    sg_putting = sum(sg_per_round) / len(sg_per_round) if sg_per_round else 0

    # --- Make % by distance (1st putt and 2nd putt) ---
    first_putt_stats: dict[str, dict] = {}
    second_putt_stats: dict[str, dict] = {}

    # Count attempts and makes for each distance
    first_putt_by_dist: dict[str, list[bool]] = defaultdict(list)
    second_putt_by_dist: dict[str, list[bool]] = defaultdict(list)

    for h in holes:
        hole_putts = sorted(putts_by_hole[h.id], key=lambda p: p.putt_number)
        if not hole_putts:
            continue

        first_dist = hole_putts[0].distance

        # 1st putt: made if total putts == 1
        first_putt_by_dist[first_dist].append(h.putts_taken == 1)

        # 2nd putt make %: given 1st putt from this distance was missed,
        # did the player hole out in 2 putts? (i.e., didn't 3-putt)
        if h.putts_taken >= 2:
            second_putt_by_dist[first_dist].append(h.putts_taken == 2)

    for dist in DISTANCES:
        attempts = first_putt_by_dist.get(dist, [])
        if attempts:
            first_putt_stats[dist] = {
                "attempts": len(attempts),
                "makes": sum(attempts),
                "pct": round(sum(attempts) / len(attempts) * 100, 1),
            }
        else:
            first_putt_stats[dist] = {"attempts": 0, "makes": 0, "pct": 0}

        attempts2 = second_putt_by_dist.get(dist, [])
        if attempts2:
            second_putt_stats[dist] = {
                "attempts": len(attempts2),
                "makes": sum(attempts2),
                "pct": round(sum(attempts2) / len(attempts2) * 100, 1),
            }
        else:
            second_putt_stats[dist] = {"attempts": 0, "makes": 0, "pct": 0}

    # --- Bucketed make percentages for gauges ---
    def _bucket_make_pct(distances: list[str]) -> float:
        total_attempts = 0
        total_makes = 0
        for d in distances:
            data = first_putt_by_dist.get(d, [])
            total_attempts += len(data)
            total_makes += sum(data)
        return round(total_makes / total_attempts * 100, 1) if total_attempts else 0

    make_pct_3ft = _bucket_make_pct(["3ft"])
    make_pct_4_5ft = _bucket_make_pct(["4ft", "5ft"])
    make_pct_6_7ft = _bucket_make_pct(["6ft", "7ft"])

    return {
        "total_rounds": len(rounds),
        "putts_per_round": round(putts_per_round, 1),
        "up_and_down_pct": round(up_and_down_pct, 1),
        "non_gir_approach_ft": round(non_gir_approach_avg, 2),
        "non_gir_approach_display": _feet_to_display(non_gir_approach_avg),
        "gir_approach_ft": round(gir_approach_avg, 2),
        "gir_approach_display": _feet_to_display(gir_approach_avg),
        "sg_putting": round(sg_putting, 2),
        "make_pct_3ft": make_pct_3ft,
        "make_pct_4_5ft": make_pct_4_5ft,
        "make_pct_6_7ft": make_pct_6_7ft,
        "first_putt_stats": first_putt_stats,
        "second_putt_stats": second_putt_stats,
        "goals": GOALS,
    }


def _empty_stats() -> dict:
    """Return empty stats structure when no data exists."""
    empty_dist = {d: {"attempts": 0, "makes": 0, "pct": 0} for d in DISTANCES}
    return {
        "total_rounds": 0,
        "putts_per_round": 0,
        "up_and_down_pct": 0,
        "non_gir_approach_ft": 0,
        "non_gir_approach_display": "0'0\"",
        "gir_approach_ft": 0,
        "gir_approach_display": "0'0\"",
        "sg_putting": 0,
        "make_pct_3ft": 0,
        "make_pct_4_5ft": 0,
        "make_pct_6_7ft": 0,
        "first_putt_stats": empty_dist,
        "second_putt_stats": empty_dist,
        "goals": GOALS,
    }
