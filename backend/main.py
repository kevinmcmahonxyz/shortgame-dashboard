import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application

from backend.config import settings
from backend.storage.database import init_db
from backend.bot.handlers import build_bot_app
from backend.api.stats import router as stats_router

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

bot_app: Application | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    init_db()
    logger.info("Database initialized")

    if settings.telegram_bot_token:
        bot_app = build_bot_app()
        await bot_app.initialize()

        if settings.bot_mode == "webhook":
            webhook_url = f"{settings.webhook_url}/webhook"
            await bot_app.bot.set_webhook(url=webhook_url)
            await bot_app.start()
            logger.info(f"Bot started in webhook mode: {webhook_url}")
        else:
            await bot_app.start()
            await bot_app.updater.start_polling()
            logger.info("Bot started in polling mode")
    else:
        logger.warning("No TELEGRAM_BOT_TOKEN set, bot disabled")

    yield

    if bot_app:
        if settings.bot_mode == "polling" and bot_app.updater:
            await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Bot stopped")


app = FastAPI(title="Shortgame Dashboard", lifespan=lifespan)

app.include_router(stats_router)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    if bot_app is None:
        return JSONResponse({"error": "Bot not configured"}, status_code=503)
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return JSONResponse({"ok": True})


# Serve frontend static files last (catch-all)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
