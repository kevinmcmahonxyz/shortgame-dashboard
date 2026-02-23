"""Construct seed data to match exact Grint averages.

Targets: 32.8 PPR, 47% GIR, 33% scramble
Make rates: 76%@3ft, 68%@4ft, 60%@5ft, 52%@6ft, 43%@7ft, 36%@8ft, 28%@10ft
3-putt rates: 3%@30ft, 50%@40ft, 42%@50ft, 66%@50ft+
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

TOTAL_ROUNDS = 24
HOLES_PER_ROUND = 18
TOTAL_HOLES = 432
TARGET_PPR = 32.8
TARGET_TOTAL_PUTTS = round(TARGET_PPR * TOTAL_ROUNDS)  # 787

# Exact outcome counts per distance (hand-tuned to hit targets)
# Format: (count, makes, two_putts, three_putts)
OUTCOMES = {
    "Gimmie": (7,   7,  0,  0),   # 100% make
    "3ft":    (25, 19,  6,  0),   # 76.0% make
    "4ft":    (25, 17,  8,  0),   # 68.0% make
    "5ft":    (20, 12,  8,  0),   # 60.0% make
    "6ft":    (25, 13, 12,  0),   # 52.0% make
    "7ft":    (30, 13, 17,  0),   # 43.3% make
    "8ft":    (30, 11, 19,  0),   # 36.7% make
    "10ft":   (25,  7, 18,  0),   # 28.0% make
    "15ft":   (54, 10, 42,  2),   # 18.5% make, 3.7% 3-putt  (+2 makes)
    "20ft":   (50,  7, 42,  1),   # 14.0% make, 2.0% 3-putt  (+2 makes)
    "25ft":   (35,  4, 30,  1),   # 11.4% make, 2.9% 3-putt  (+2 makes)
    "30ft":   (30,  2, 27,  1),   # 6.7% make, 3.3% 3-putt   (+1 make)
    "40ft":   (24,  0, 12, 12),   # 0% make, 50.0% 3-putt
    "50ft":   (24,  0, 14, 10),   # 0% make, 41.7% 3-putt
    "50ft+":  (28,  0, 10, 18),   # 0% make, 64.3% 3-putt
}

LEAVE_POOLS = {
    "3ft": ["Gimmie", "3ft"],
    "4ft": ["Gimmie", "3ft", "3ft", "4ft"],
    "5ft": ["3ft", "3ft", "4ft", "4ft"],
    "6ft": ["3ft", "3ft", "4ft", "4ft", "5ft"],
    "7ft": ["3ft", "4ft", "4ft", "5ft", "5ft"],
    "8ft": ["3ft", "4ft", "5ft", "5ft", "6ft"],
    "10ft": ["4ft", "5ft", "5ft", "6ft", "6ft", "7ft"],
    "15ft": ["4ft", "5ft", "6ft", "6ft", "7ft", "8ft"],
    "20ft": ["5ft", "6ft", "7ft", "7ft", "8ft", "10ft"],
    "25ft": ["5ft", "6ft", "7ft", "8ft", "8ft", "10ft"],
    "30ft": ["6ft", "7ft", "8ft", "8ft", "10ft", "15ft"],
    "40ft": ["7ft", "8ft", "10ft", "10ft", "15ft", "20ft"],
    "50ft": ["8ft", "10ft", "10ft", "15ft", "15ft", "20ft"],
    "50ft+": ["10ft", "15ft", "15ft", "20ft", "20ft", "25ft"],
}


def construct():
    # Verify counts
    total_holes = sum(v[0] for v in OUTCOMES.values())
    assert total_holes == TOTAL_HOLES, f"Total holes {total_holes} != {TOTAL_HOLES}"
    for dist, (n, makes, twos, threes) in OUTCOMES.items():
        assert makes + twos + threes == n, f"{dist}: {makes}+{twos}+{threes} != {n}"

    total_putts = sum(m + 2*t + 3*th for _, (_, m, t, th) in OUTCOMES.items())
    ppr = total_putts / TOTAL_ROUNDS
    print(f"Total putts: {total_putts}, PPR: {ppr:.2f}")

    # Build flat list of holes
    holes = []
    for dist, (n, makes, twos, threes) in OUTCOMES.items():
        for _ in range(makes):
            holes.append({"first_dist": dist, "putts_taken": 1, "putt_dists": [dist]})
        for _ in range(twos):
            leave = random.choice(LEAVE_POOLS.get(dist, ["3ft"]))
            holes.append({"first_dist": dist, "putts_taken": 2, "putt_dists": [dist, leave]})
        for _ in range(threes):
            leave1 = random.choice(LEAVE_POOLS.get(dist, ["3ft"]))
            leave2 = random.choice(LEAVE_POOLS.get(leave1, ["3ft"]))
            holes.append({"first_dist": dist, "putts_taken": 3, "putt_dists": [dist, leave1, leave2]})

    random.shuffle(holes)

    # Assign GIR: 47% = 203 GIR holes
    gir_count = round(TOTAL_HOLES * 0.47)  # 203
    non_gir_count = TOTAL_HOLES - gir_count  # 229

    # Up & Down: 33% of non-GIR = 76 one-putts on non-GIR
    scramble_count = round(non_gir_count * 0.33)  # 76

    one_putt_holes = [i for i, h in enumerate(holes) if h["putts_taken"] == 1]
    multi_putt_holes = [i for i, h in enumerate(holes) if h["putts_taken"] >= 2]
    random.shuffle(one_putt_holes)
    random.shuffle(multi_putt_holes)

    gir_flags = [False] * TOTAL_HOLES

    # Assign GIR to some 1-putt holes (these are birdie putts made)
    gir_one_putts = min(len(one_putt_holes) - scramble_count, gir_count)
    for idx in one_putt_holes[:gir_one_putts]:
        gir_flags[idx] = True

    # Non-GIR 1-putts = scramble (up-and-downs)
    # (remaining 1-putt holes stay non-GIR)

    # Fill remaining GIR quota from multi-putt holes
    remaining_gir = gir_count - gir_one_putts
    for idx in multi_putt_holes[:remaining_gir]:
        gir_flags[idx] = True

    # Distribute into 24 rounds of 18 holes
    rounds_data = []
    today = date.today()
    days_span = 180

    for r in range(TOTAL_ROUNDS):
        days_ago = int(days_span * (1 - r / (TOTAL_ROUNDS - 1)))
        round_date = today - timedelta(days=days_ago)
        round_holes = []

        for h_idx in range(HOLES_PER_ROUND):
            flat_idx = r * HOLES_PER_ROUND + h_idx
            h = holes[flat_idx]
            round_holes.append({
                "hole_number": h_idx + 1,
                "gir": gir_flags[flat_idx],
                "putts_taken": h["putts_taken"],
                "putts": [
                    {"putt_number": i + 1, "distance": d}
                    for i, d in enumerate(h["putt_dists"])
                ],
            })

        rounds_data.append({
            "date": round_date.isoformat(),
            "course_name": f"Seed Round {r + 1}",
            "holes": round_holes,
        })

    # Verify stats
    all_holes = [h for rd in rounds_data for h in rd["holes"]]
    total_putts_check = sum(h["putts_taken"] for h in all_holes)
    gir_holes = [h for h in all_holes if h["gir"]]
    non_gir = [h for h in all_holes if not h["gir"]]
    scrambles = sum(1 for h in non_gir if h["putts_taken"] == 1)

    print(f"\nVerification:")
    print(f"  Rounds: {len(rounds_data)}")
    print(f"  Total holes: {len(all_holes)}")
    print(f"  Total putts: {total_putts_check}")
    print(f"  PPR: {total_putts_check / TOTAL_ROUNDS:.2f}")
    print(f"  GIR: {len(gir_holes)}/{len(all_holes)} = {len(gir_holes)/len(all_holes)*100:.1f}%")
    print(f"  Up & Down: {scrambles}/{len(non_gir)} = {scrambles/len(non_gir)*100:.1f}%")

    # Make rates by distance
    from collections import defaultdict
    first_by_dist = defaultdict(list)
    three_putt_by_dist = defaultdict(lambda: [0, 0])  # [total, 3putts]
    for h in all_holes:
        fd = h["putts"][0]["distance"]
        first_by_dist[fd].append(h["putts_taken"] == 1)
        three_putt_by_dist[fd][0] += 1
        if h["putts_taken"] >= 3:
            three_putt_by_dist[fd][1] += 1

    print(f"\n  Make rates:")
    for dist in OUTCOMES:
        data = first_by_dist.get(dist, [])
        if data:
            print(f"    {dist}: {sum(data)}/{len(data)} = {sum(data)/len(data)*100:.1f}%")

    print(f"\n  3-putt rates:")
    for dist in ["30ft", "40ft", "50ft", "50ft+"]:
        total, threes = three_putt_by_dist[dist]
        if total:
            print(f"    {dist}: {threes}/{total} = {threes/total*100:.1f}%")

    return {"rounds": rounds_data}


if __name__ == "__main__":
    data = construct()
    out = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nWrote {out}")
