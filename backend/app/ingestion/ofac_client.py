"""
OFAC (US Treasury) Specially Designated Nationals list connector.
Free, public, no API key: https://sanctionslist.ofac.treas.gov/Home/SdnList
We pull the CSV feed and filter for entries relevant to shipping/energy
(vessel entries, oil-trading entities) so the Risk Agent can factor
sanctions-list deltas into its scoring.
"""
import logging
import csv
import io
import httpx

logger = logging.getLogger("sentinel.ingestion.ofac")

OFAC_SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"

ENERGY_KEYWORDS = ["tanker", "oil", "petroleum", "shipping", "vessel", "crude", "NIOC", "tanker"]


async def fetch_energy_related_sanctions(limit: int = 50) -> list[dict]:
    """
    Downloads the OFAC SDN CSV and returns entries whose remarks/name
    mention shipping or oil-trading terms. Returns [] gracefully on any
    network failure so ingestion never blocks on this optional source.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(OFAC_SDN_CSV_URL)
            resp.raise_for_status()
            text = resp.text
    except Exception as exc:  # noqa: BLE001
        logger.warning("OFAC SDN fetch failed: %s", exc)
        return []

    results = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 3:
            continue
        joined = " ".join(row).lower()
        if any(kw.lower() in joined for kw in ENERGY_KEYWORDS):
            results.append({"raw_row": row[:5]})
            if len(results) >= limit:
                break
    return results
