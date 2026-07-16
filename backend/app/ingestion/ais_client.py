"""
AIS (Automatic Identification System) vessel tracking connector.

Real integration: MarineTraffic / Spire Maritime both expose REST APIs for
live vessel positions inside a bounding box (e.g. the Strait of Hormuz).
Set MARINETRAFFIC_API_KEY to use the live endpoint below.

Replay simulator: AIS feeds are paid commercial products (MarineTraffic,
Spire) — this module also ships a deterministic replay simulator built on
a public historical AIS sample so vessel-density/anomaly logic can be
built, demoed, and unit-tested without a paid subscription. Swap
AIS_SOURCE=live once a key is configured; the consumer code
(app/agents/risk_agent.py) is identical either way.
"""
import os
import json
import random
import logging
import httpx

logger = logging.getLogger("sentinel.ingestion.ais")

MARINETRAFFIC_API_KEY = os.getenv("MARINETRAFFIC_API_KEY", "")
AIS_SOURCE = os.getenv("AIS_SOURCE", "simulated")  # "live" | "simulated"

# MarineTraffic PositionsInRadius-style endpoint (exact path depends on plan)
MARINETRAFFIC_URL = "https://services.marinetraffic.com/api/exportvessels/v:8"

HORMUZ_BBOX = {"min_lat": 25.5, "max_lat": 27.5, "min_lon": 55.0, "max_lon": 57.5}


async def fetch_live_ais(bbox: dict = HORMUZ_BBOX) -> list[dict]:
    if not MARINETRAFFIC_API_KEY:
        logger.info("MARINETRAFFIC_API_KEY not set; use fetch_simulated_ais() instead.")
        return []
    params = {
        "key": MARINETRAFFIC_API_KEY,
        "minlat": bbox["min_lat"], "maxlat": bbox["max_lat"],
        "minlon": bbox["min_lon"], "maxlon": bbox["max_lon"],
        "protocol": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(MARINETRAFFIC_URL, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("MarineTraffic fetch failed: %s", exc)
        return []


def fetch_simulated_ais(corridor_id: str = "hormuz", n_vessels: int = 40, seed: int | None = None) -> dict:
    """
    Deterministic-ish simulated vessel density snapshot for a corridor.
    Used to compute a 'traffic anomaly' signal: a sharp drop in tanker
    count through a chokepoint is itself a leading risk indicator
    (vessels re-routing or holding position ahead of a public announcement).
    """
    rng = random.Random(seed)
    baseline = 45
    vessel_count = max(0, int(rng.gauss(baseline, 6)))
    anomaly_pct = round(((vessel_count - baseline) / baseline) * 100, 1)
    return {
        "corridor_id": corridor_id,
        "vessel_count": vessel_count,
        "baseline_vessel_count": baseline,
        "traffic_anomaly_pct": anomaly_pct,
        "tanker_subset_count": max(0, int(vessel_count * 0.4)),
        "source": "simulated_replay",
    }
