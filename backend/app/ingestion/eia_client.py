"""
US EIA (Energy Information Administration) connector for Brent/WTI spot prices.
Free API, requires a free key from https://www.eia.gov/opendata/register.php
Set EIA_API_KEY in the environment. Docs: https://www.eia.gov/opendata/documentation.php
"""
import os
import logging
import httpx

logger = logging.getLogger("sentinel.ingestion.eia")

EIA_API_KEY = os.getenv("EIA_API_KEY", "")
EIA_BRENT_SERIES = "https://api.eia.gov/v2/petroleum/pri/spt/data/"


async def fetch_brent_price() -> dict | None:
    """Fetch latest Brent spot price. Returns None gracefully if no key/network."""
    if not EIA_API_KEY:
        logger.info("EIA_API_KEY not set; skipping live price fetch.")
        return None
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": "RBRTE",  # Europe Brent Spot Price FOB
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(EIA_BRENT_SERIES, params=params)
            resp.raise_for_status()
            data = resp.json()
            rows = data.get("response", {}).get("data", [])
            if rows:
                return {"period": rows[0]["period"], "usd_per_bbl": rows[0]["value"]}
    except Exception as exc:  # noqa: BLE001
        logger.warning("EIA price fetch failed: %s", exc)
    return None
