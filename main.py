import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from scrapers import fetch_all

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

INTERVALS = {
    "hourly":      3600,
    "twice_daily": 43200,
    "daily":       86400,
}

# ── State ──────────────────────────────────────────────────────────────────────
cache: dict = {"models": {}, "last_updated": None, "status": "pending"}
config: dict = {"polling_interval": "daily"}
scheduler = AsyncIOScheduler()


def load_config():
    global config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


async def poll():
    cache["status"] = "polling"
    try:
        data = await fetch_all()
        cache["models"] = data
        cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        cache["status"] = "ok"
    except Exception as exc:
        cache["status"] = "error"
        cache["error"] = str(exc)


def reschedule(interval_name: str):
    scheduler.remove_all_jobs()
    seconds = INTERVALS.get(interval_name, INTERVALS["daily"])
    scheduler.add_job(poll, "interval", seconds=seconds, id="poll_job")


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_config()
    scheduler.start()
    reschedule(config.get("polling_interval", "daily"))
    asyncio.create_task(poll())          # initial poll on startup
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


# ── API routes (must come before static mount) ─────────────────────────────────
@app.get("/api/models")
async def get_models():
    return JSONResponse(
        {"models": cache["models"], "last_updated": cache["last_updated"],
         "status": cache["status"]}
    )


@app.get("/api/config")
async def get_config():
    return JSONResponse(config)


@app.put("/api/config")
async def update_config(request: Request):
    body = await request.json()
    interval = body.get("polling_interval", "")
    if interval in INTERVALS:
        config["polling_interval"] = interval
        save_config()
        reschedule(interval)
    return JSONResponse(config)


@app.post("/api/refresh")
async def manual_refresh():
    asyncio.create_task(poll())
    return JSONResponse({"status": "polling started"})


# ── Static files (SPA fallback) ───────────────────────────────────────────────
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"),
                           html=True), name="static")
