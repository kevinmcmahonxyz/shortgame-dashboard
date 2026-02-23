# Shortgame Dashboard

Personal golf shortgame statistics tracker. Collects putting data via a
Telegram bot during rounds and displays performance metrics on a web dashboard.

## Why

The Grint tracks basic stats but lacks putting granularity. This tool tracks
every putt distance per hole, calculates Strokes Gained: Putting against PGA
Tour baselines, and visualizes trends over time. 24 rounds of seed data
(calibrated to historical Grint averages) ensure new entries are weighted
against prior performance.

## Architecture

Single-process Python app (FastAPI + uvicorn) serving:
- **Telegram bot webhook** (`/webhook`) - inline keyboard flow for hole-by-hole putt entry
- **REST API** (`/api/stats`) - computed dashboard statistics
- **Static frontend** (`/`) - vanilla HTML/CSS/JS dashboard with SVG gauges

## Tech Stack

- **Backend**: FastAPI, python-telegram-bot v21+, SQLModel, SQLite
- **Frontend**: Vanilla HTML/CSS/JS (no build step), SVG circular gauges
- **Infra**: Docker, Cloudflare Tunnel or ngrok for public HTTPS

## Project Layout

- `backend/main.py` - FastAPI app, lifespan, webhook endpoint
- `backend/bot/handlers.py` - Telegram ConversationHandler state machine (HOLE_COUNT → FIRST_PUTT → GIR_SELECT → NEXT_PUTT)
- `backend/bot/keyboards.py` - Inline keyboard builders (distance, GIR, 9/18 holes)
- `backend/services/stats_service.py` - All stat calculations (PPR, SG:Putt, make %, up-and-down, approach distance)
- `backend/storage/database.py` - SQLModel models (Round, Hole, Putt)
- `backend/constants.py` - Distance lists, SG baseline table, goal thresholds
- `frontend/` - Static dashboard (index.html, CSS, JS)
- `data/seed_data.json` - Fixed seed data fixture (24 rounds matching Grint averages)
- `scripts/seed_dummy_data.py` - Load seed data from fixture into DB
- `scripts/construct_seed.py` - One-time script that built the seed fixture

## Commands

- `docker compose up` - Run locally
- `uvicorn backend.main:app --reload --port 8000` - Dev mode (no Docker)
- `python -m scripts.seed_dummy_data` - Load seed data from fixture into DB

## Bot Commands

- `/round` - Start a new round (choose 9 or 18 holes)
- `/cancel` - End current round early (completed holes are saved)
- `/help` - Show usage instructions

## Key Stats Tracked

- Putts Per Round (goal: <31.8)
- Up & Down % (goal: 50%)
- Non-GIR Approach Distance (goal: <7ft)
- Strokes Gained: Putting (vs PGA Tour baseline)
- Make % at 3ft (goal: 90%), 4-5ft (goal: 70%), 6-7ft (goal: 50%)

## Baseline Performance (from The Grint, 24 rounds)

- 32.8 putts/round, 47% GIR, 33% scrambling
- Make rates: 76% @ 3ft, 60% @ 5ft, 43% @ 7ft, 28% @ 10ft
- 3-putt rates: 3% @ 30ft, 50% @ 40ft, 42% @ 50ft, 66% @ 50ft+

## Conventions

- Distance stored as label strings ("3ft", "50ft+", "Gimmie") matching keyboard buttons
- SG:Putting formula: expected_putts(1st_putt_distance) - actual_putts_taken
- Non-GIR approach distance = 1st putt distance in non-GIR situations (real rounds only, excludes seed data)
- "Made It!" (distance "0") means previous putt went in; actual_putts = putt_num - 1
- Seed rounds flagged with `is_seed=True`, loaded from `data/seed_data.json`
- 9-hole rounds normalized to 18-hole equivalents for PPR and SG stats
- Bot uses polling mode locally, webhook mode in production (controlled by BOT_MODE env var)
