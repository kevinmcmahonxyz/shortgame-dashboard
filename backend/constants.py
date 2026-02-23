# Distance labels used on inline keyboards and stored in DB
DISTANCES = [
    "Gimmie", "3ft", "4ft", "5ft",
    "6ft", "7ft", "8ft", "10ft",
    "15ft", "20ft", "25ft", "30ft",
    "40ft", "50ft", "50ft+",
]

# Distance labels to numeric feet (midpoint estimates for averaging)
DISTANCE_TO_FEET: dict[str, float] = {
    "Gimmie": 2.0,
    "3ft": 3.0,
    "4ft": 4.0,
    "5ft": 5.0,
    "6ft": 6.0,
    "7ft": 7.0,
    "8ft": 8.0,
    "10ft": 10.0,
    "15ft": 15.0,
    "20ft": 20.0,
    "25ft": 25.0,
    "30ft": 30.0,
    "40ft": 40.0,
    "50ft": 50.0,
    "50ft+": 60.0,
}

# PGA Tour baseline expected putts (Mark Broadie)
SG_BASELINE: dict[str, float] = {
    "Gimmie": 1.009,
    "3ft": 1.053,
    "4ft": 1.147,
    "5ft": 1.256,
    "6ft": 1.350,
    "7ft": 1.443,
    "8ft": 1.500,
    "10ft": 1.626,
    "15ft": 1.790,
    "20ft": 1.878,
    "25ft": 1.934,
    "30ft": 1.978,
    "40ft": 2.055,
    "50ft": 2.135,
    "50ft+": 2.150,
}

# Dashboard goal thresholds
GOALS = {
    "putts_per_round": 31.8,
    "up_and_down_pct": 50.0,
    "non_gir_approach_ft": 7.0,  # feet
    "sg_putting": 0.0,
    "make_pct_3ft": 90.0,
    "make_pct_4_5ft": 70.0,
    "make_pct_6_7ft": 50.0,
}
