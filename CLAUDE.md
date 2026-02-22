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
- `backend/bot/handlers.py` - Telegram ConversationHandler state machine
- `backend/bot/keyboards.py` - Inline keyboard builders
- `backend/services/stats_service.py` - All stat calculations (PPR, SG:Putt, make %, up-and-down)
- `backend/storage/database.py` - SQLModel models (Round, Hole, Putt)
- `backend/constants.py` - Distance lists, SG baseline table, goal thresholds
- `frontend/` - Static dashboard (index.html, CSS, JS)
- `scripts/seed_dummy_data.py` - Generate 24 seed rounds

## Commands

- `docker compose up` - Run locally
- `uvicorn backend.main:app --reload --port 8000` - Dev mode (no Docker)
- `python -m scripts.seed_dummy_data` - Seed 24 dummy rounds

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
- Non-GIR approach distance = 1st putt distance in non-GIR situations
- Seed rounds flagged with `is_seed=True`
- Bot uses polling mode locally, webhook mode in production (controlled by BOT_MODE env var)
