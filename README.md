# SENTINEL — AI-Driven Energy Supply Chain Resilience Platform

A working, tested full-stack implementation of the Energy Supply Chain Intelligence
challenge: it monitors geopolitical/logistics risk, models disruption scenarios,
and generates ranked, executable procurement rerouting recommendations —
with strategic reserve drawdown guidance — for India's crude oil import network.

This is real, running code (backend fully tested with `pytest`, frontend
builds clean with `tsc` + `vite build`), not a mockup. See `docs/known-limitations.md`
for an honest account of what's simulated vs. live in this build.

---

## 1. Fastest way to see it running (no external accounts needed)

```bash
docker-compose -f docker-compose.quickstart.yml up --build
```
- Backend: http://localhost:8000 (docs at http://localhost:8000/docs)
- Frontend: http://localhost:5173

This runs on SQLite + an in-memory knowledge graph + an in-process event bus —
zero external services required. The backend auto-replays realistic sample
events every 20 seconds so the War Room dashboard feels alive immediately.

## 2. Full production stack (Postgres + Neo4j + Kafka)

```bash
docker-compose up --build
```
This spins up Postgres, Neo4j, Zookeeper+Kafka, the backend, and the frontend.
The backend feature-detects each service via environment variables already
set in `docker-compose.yml` and switches from its in-process fallbacks to
the real infrastructure automatically — no code changes needed.

To enable live external data (optional, all free tiers):
- `EIA_API_KEY` — free key at https://www.eia.gov/opendata/register.php (Brent/WTI prices)
- `MARINETRAFFIC_API_KEY` — paid; without it, AIS uses a deterministic replay simulator
- GDELT and OFAC sources need no key at all

## 3. Running without Docker (local dev)

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Then open http://localhost:5173 (Vite dev server proxies API calls to
`http://localhost:8000` per `.env`).

**Run the test suite:**
```bash
cd backend && source venv/bin/activate
pytest app/tests/test_api.py -v
```
All 10 tests should pass — they exercise the full M1→M2→M3→M4 chain, auth,
and every API contract endpoint.

## 4. Live demo script (what to click)

1. Open the **War Room** — you'll see the corridor risk map and live alert feed.
2. Click **"Inject test disruption signal"** — this fires a real event through
   the ingestion bus, which the Orchestrator picks up and runs through all
   four agents in real time (watch the alert feed update via WebSocket).
3. Go to **Scenario Simulator**, pick "Strait of Hormuz — Partial Closure,"
   adjust the sliders, and click **Run simulation** — watch the cascade
   (refinery run-rate → fuel price → power sector → GDP), then click
   **"Show your work"** to see every coefficient used.
4. Click **"View procurement options"** — see the MILP-ranked alternative
   suppliers with real cost/delay/risk tradeoffs, and **Execute** one.
5. Click **"View reserve impact"** — see the LP-optimized SPR drawdown schedule.
6. Go to **Agent Trace** — see the full explainability chain and the live
   signal-to-recommendation latency metric, computed from real trace data.

---

## Repository layout

```
sentinel/
├── backend/            # FastAPI + agents + ML/optimization + graph + ingestion
│   ├── app/
│   │   ├── agents/      # M1-M4 agent logic + orchestrator + assumptions ledger
│   │   ├── ml/           # scoring.py (risk math), optimization.py (MILP/LP)
│   │   ├── graph/        # Neo4j client with in-memory NetworkX fallback
│   │   ├── ingestion/    # GDELT / EIA / OFAC / AIS connectors + Kafka event bus
│   │   ├── db/            # SQLAlchemy models, seed loader
│   │   ├── auth/          # JWT auth, password hashing, role-based access
│   │   ├── api/routes/    # REST endpoints (see docs/api-contract.md)
│   │   ├── websocket/    # live push connection manager
│   │   └── tests/         # pytest suite (10 tests, all passing)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── pages/         # Dashboard, ScenarioSimulator, ProcurementConsole,
│       │                  # ReservePlanner, TraceView
│       ├── components/    # Shell, CorridorMap (Leaflet), AlertFeed, ui primitives
│       ├── hooks/          # useLiveFeed (WebSocket)
│       └── api/            # typed REST client
├── data/                # seed datasets (corridors, suppliers, refineries, events, baseline)
├── docs/                # architecture doc, API contract, assumptions ledger, known limitations
├── docker-compose.yml               # full production stack
├── docker-compose.quickstart.yml    # zero-infra instant demo
└── README.md            # this file
```

## Architecture

See `docs/architecture.md` and `docs/system-architecture.mermaid` for the
full layered architecture diagram and team-by-team breakdown this project
was built from.

## Assumptions ledger

Every coefficient the system uses (fuel price elasticity, GDP sensitivity,
SPR floor reserve, MILP objective weights, etc.) is centralized and
documented with its source rationale in `backend/app/agents/assumptions.py`.
This is deliberate: the challenge brief scores "scenario model fidelity"
on whether assumptions are explicit and testable, not on model complexity.
