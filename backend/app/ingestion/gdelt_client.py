"""
GDELT Project connector — free, no-API-key geopolitical event feed.
Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

Real HTTP calls against the GDELT DOC 2.0 API. Runs fully offline-capable
too: if the request fails (no network egress, rate limited, etc.) the
caller receives an empty list rather than raising, and the local sample
events in data/events_sample.json are used instead so the pipeline never
stalls on an external dependency during a demo.
"""
import logging
import httpx

logger = logging.getLogger("sentinel.ingestion.gdelt")

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERY_TERMS = [
    "Strait of Hormuz",
    "Red Sea shipping attack",
    "OPEC emergency",
    "Iran oil sanctions",
    "India crude oil imports",
]


async def fetch_recent_events(max_records: int = 25) -> list[dict]:
    """Query GDELT for recent articles matching our energy-security terms."""
    results: list[dict] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for term in QUERY_TERMS:
            try:
                resp = await client.get(GDELT_DOC_API, params={
                    "query": term,
                    "mode": "artlist",
                    "maxrecords": max_records,
                    "format": "json",
                })
                resp.raise_for_status()
                payload = resp.json()
                for article in payload.get("articles", []):
                    results.append({
                        "source": "GDELT",
                        "headline": article.get("title"),
                        "raw_text": article.get("title", ""),
                        "url": article.get("url"),
                        "timestamp": article.get("seendate"),
                        "query_term": term,
                    })
            except Exception as exc:  # noqa: BLE001
                logger.warning("GDELT fetch failed for '%s': %s", term, exc)
                continue
    return results
