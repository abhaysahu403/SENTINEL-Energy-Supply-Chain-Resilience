"""
Background task that, when enabled, periodically replays the sample
historical events (data/events_sample.json) through the real ingestion
bus -- this is what makes the War-Room Dashboard feel 'alive' during a
demo without requiring a live paid news/AIS subscription to be configured.
Disable by setting SENTINEL_AUTOPLAY=0.
"""
import os
import json
import random
import asyncio
import logging
import datetime as dt

from app.config import DATA_DIR, SIMULATOR_INTERVAL_SECONDS
from app.ingestion.event_bus import publish_event

logger = logging.getLogger("sentinel.simulator")

AUTOPLAY = os.getenv("SENTINEL_AUTOPLAY", "1") == "1"


def _load_sample_events() -> list[dict]:
    with open(DATA_DIR / "events_sample.json") as f:
        return json.load(f)


async def run_autoplay_loop():
    if not AUTOPLAY:
        logger.info("Autoplay disabled (SENTINEL_AUTOPLAY=0).")
        return
    events = _load_sample_events()
    logger.info("Autoplay enabled: replaying %d sample events every %ss", len(events), SIMULATOR_INTERVAL_SECONDS)
    idx = 0
    await asyncio.sleep(5)  # let the app finish booting first
    while True:
        event = dict(events[idx % len(events)])
        event["id"] = f"{event['id']}_replay_{dt.datetime.utcnow().timestamp():.0f}"
        event["timestamp"] = dt.datetime.utcnow().isoformat()
        # small jitter on severity so repeated replays aren't identical
        event["severity"] = max(5.0, min(100.0, event["severity"] + random.uniform(-8, 8)))
        await publish_event(event)
        idx += 1
        await asyncio.sleep(SIMULATOR_INTERVAL_SECONDS)
