# Known Limitations & What's Simulated vs. Live

Being upfront about this matters more than pretending otherwise — here's
exactly what's real and what's a stand-in, and how to flip each one on.

| Component | This build | To go fully live |
|---|---|---|
| News/geopolitical events | Real GDELT API integration (`app/ingestion/gdelt_client.py`) + a curated replay of realistic sample events for demo continuity | Already live — GDELT needs no key. For paid premium news APIs, add a client alongside it |
| Commodity prices | Real EIA API integration, returns `None` gracefully without a key | Get a free key at eia.gov/opendata |
| Sanctions data | Real OFAC SDN CSV download, live | Already live |
| AIS vessel tracking | Deterministic simulator standing in for MarineTraffic/Spire (both are paid commercial products) | Set `MARINETRAFFIC_API_KEY`; the client code (`ais_client.py`) already calls the real endpoint when present |
| Knowledge graph | Runs on Neo4j when `NEO4J_URI` is set (real Cypher queries in `knowledge_graph.py`); otherwise an in-memory NetworkX graph with an identical interface | Set `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` (docker-compose.yml already wires this) |
| Event bus | Runs on Kafka when `KAFKA_BOOTSTRAP_SERVERS` is set; otherwise an in-process asyncio queue | Set `KAFKA_BOOTSTRAP_SERVERS` (docker-compose.yml already wires this) |
| Database | SQLite by default; Postgres when `SENTINEL_DATABASE_URL` points to one | docker-compose.yml already wires Postgres for the full stack |
| Risk scoring model | Transparent weighted formula (see `assumptions.py`), not a trained classifier | Once you have labeled historical event→outcome data, swap `ml/scoring.py`'s weighted sum for a trained model (e.g. gradient boosted classifier) — the interface stays the same |
| Scenario cascade coefficients | Order-of-magnitude estimates cited to public IMF/RBI/PPAC studies, explicitly logged as assumptions | Replace with your own calibrated coefficients — every one is a named constant in `assumptions.py`, nothing is buried in code |
| Procurement "Execute" | Returns a structured order confirmation object | Wire to a real procurement/ERP system (e.g. SAP Ariba API) in `procurement_routes.py`'s `execute_recommendation` |
| Auth | Real JWT + bcrypt, not mocked | Production-ready as-is; rotate `SENTINEL_JWT_SECRET` |

## Why this design

Every "fallback" above is a genuine, load-bearing engineering pattern
(feature-detected backend), not a placeholder pretending to be real:
the Neo4j Cypher queries and Kafka producer/consumer code are exactly
what runs the moment you point the corresponding environment variable
at live infrastructure. The fallbacks exist so the whole system is
demoable and testable without requiring five paid/managed services
just to click through it once.
