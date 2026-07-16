# Project SENTINEL
### AI-Driven Energy Supply Chain Resilience Platform for Import-Dependent Economies
**CTO Architecture & Team Execution Plan — v1.0**

---

## 0. How to Use This Document

This is the single source of truth for the build. It is split into:
- **Section 1–3**: Vision, system architecture, and how the modules connect (read by everyone).
- **Section 4**: ML/Data Science team brief.
- **Section 5**: Backend team brief.
- **Section 6**: Frontend team brief.
- **Section 7**: DevOps/Infra team brief.
- **Section 8**: Cross-team API contracts (the glue — nobody builds until this is frozen).
- **Section 9**: Sprint plan and deliverable mapping to judging criteria.

Each team should read Sections 1–3 fully, then jump to their own section + Section 8.

---

## 1. Vision & Product Framing

We are not building a dashboard. We are building a **decision-support nervous system**: it senses geopolitical/logistics risk → translates it into economic impact → proposes concrete, executable alternatives → and shows a human decision-maker exactly what to do, in minutes instead of days.

**Product name (working):** SENTINEL — Strategic Energy Network Threat Intelligence & Logistics platform

**Primary user personas:**
1. **Refinery Procurement Manager** — needs alternative crude sourcing options fast.
2. **Ministry of Petroleum / SPR Policy Desk** — needs reserve drawdown decision support.
3. **Executive/War-room viewer** — needs a live situational awareness view during a crisis.

**North-star metric for the demo:** *Signal-to-recommendation time* — from a simulated geopolitical event hitting our ingestion pipeline to a ranked, executable procurement recommendation appearing on screen. Target: under 90 seconds in the live demo.

---

## 2. The Five Core Modules (mapped to the challenge brief)

| # | Module | One-line job |
|---|--------|--------------|
| M1 | **Geopolitical Risk Intelligence Agent** | Continuously ingest news/AIS/sanctions/price data → output a live Disruption Probability Score per corridor/supplier |
| M2 | **Disruption Scenario Modeller** | Simulate named scenarios (Hormuz closure, OPEC+ cut, Red Sea suspension) → cascading impact on run-rates, prices, power sector, GDP |
| M3 | **Adaptive Procurement Orchestrator** | Rank alternative crude sources/routes against spot price, tanker availability, port congestion, refinery grade compatibility |
| M4 | **Strategic Reserve Optimisation Agent** | Model optimal SPR drawdown schedules against forecast supply gaps |
| M5 | **Supply Chain Digital Twin** | Geospatial "living map" of the full network (wellhead → tanker → port → refinery → distribution) that everything else plots onto |

**Build priority for the hackathon (do NOT build all five to the same depth):**
- **Tier 1 (must be flawless):** M1, M3, M5 — these are what a judge sees and clicks on.
- **Tier 2 (must work, can be simpler models):** M2, M4 — these can run on rule-based + light ML rather than deep simulation, and still score well if assumptions are explicit (judges explicitly reward "assumptions must be explicit and testable").

---

## 3. High-Level System Architecture

### 3.1 Layered view

```
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 5 — FRONTEND (React)                                        │
│  War-room Dashboard | Scenario Simulator | Procurement Console      │
│  Digital Twin Map | Reserve Planner | Alert Feed                    │
└───────────────────────────────────────────────────────────────────┘
                              ▲  REST/WebSocket/GraphQL
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 4 — API GATEWAY / BFF (Node.js or FastAPI)                  │
│  Auth, rate limiting, request aggregation, WebSocket fan-out        │
└───────────────────────────────────────────────────────────────────┘
                              ▲
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 3 — AGENT ORCHESTRATION (Python, LangGraph/CrewAI-style)    │
│  Risk Agent | Scenario Agent | Procurement Agent | Reserve Agent    │
│  Orchestrator Agent (routes events → agents → recommendations)      │
└───────────────────────────────────────────────────────────────────┘
                              ▲
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 2 — INTELLIGENCE & DATA SERVICES                            │
│  RAG pipeline | Knowledge Graph (Neo4j) | Forecasting models        │
│  Optimization engine (LP/MILP) | Vector DB | Feature store          │
└───────────────────────────────────────────────────────────────────┘
                              ▲
┌───────────────────────────────────────────────────────────────────┐
│  LAYER 1 — DATA INGESTION                                          │
│  News/RSS scrapers | AIS vessel feeds | Sanctions registries        │
│  Commodity price APIs | Port/refinery static data                   │
└───────────────────────────────────────────────────────────────────┘
```

### 3.2 End-to-end data flow (the "money path" for the demo)

1. **Ingestion** — a news event or simulated AIS anomaly enters Layer 1.
2. **Risk Agent (M1)** — LLM extracts entities (corridor, supplier, event type), updates Disruption Probability Score in the Knowledge Graph.
3. **Orchestrator Agent** — sees the score cross a threshold → triggers Scenario Agent (M2).
4. **Scenario Agent** — runs the closest-matching pre-built scenario template, produces impact numbers (refinery run-rate delta, price delta, days-of-cover remaining).
5. **Procurement Agent (M3)** — queries alternative supplier/route database, ranks options against live constraints, returns top 3 executable options with cost/time/risk tradeoffs.
6. **Reserve Agent (M4)** — checks if SPR drawdown is advisable given the new supply gap, proposes a schedule.
7. **Frontend** — all of the above streams into the War-room dashboard via WebSocket, with the Digital Twin map (M5) highlighting affected routes in real time.

### 3.3 Recommended tech stack (final — teams should not re-litigate this)

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + TypeScript, Vite, TailwindCSS, shadcn/ui, deck.gl / Mapbox GL for geospatial, Recharts/D3 for charts | Fast to build, strong geospatial + charting ecosystem |
| Realtime | WebSockets (Socket.IO) + REST fallback | Push live risk score updates without polling |
| BFF/Gateway | FastAPI (Python) | Same language as ML layer, minimal glue code |
| Agent orchestration | LangGraph (or CrewAI) on top of an LLM API (Claude) | Multi-agent state machines with explicit tool calls |
| Knowledge Graph | Neo4j (or ArangoDB) | Supplier–route–risk–refinery relationships, path queries for rerouting |
| Vector DB / RAG | Qdrant or pgvector | Semantic search over news/sanctions/policy text |
| Forecasting/ML | Python: scikit-learn, XGBoost, Prophet/statsmodels for time series, PyTorch optional for NLP fine-tuning | Interpretable models score better on "explicit, testable assumptions" |
| Optimization | PuLP / OR-Tools (MILP) for procurement ranking & SPR drawdown scheduling | Real optimization > heuristic scoring, and defensible to judges |
| Data pipeline | Apache Airflow (or Prefect) for scheduled ingestion; Kafka optional if time permits for streaming | Reliability, visible pipeline for architecture diagram |
| Database | PostgreSQL (transactional) + TimescaleDB extension (time series prices/risk scores) | One DB to operate, time-series native |
| Infra | Docker Compose for dev, deployable to AWS/GCP (ECS/Cloud Run) for demo hosting | Judge-accessible live demo |
| Auth | Auth0 or simple JWT (hackathon scope — keep light) | Don't over-engineer |

---

## 4. ML / DATA SCIENCE TEAM BRIEF

### 4.1 Mission
Turn messy, multi-source signals into (a) a live risk score, (b) scenario impact numbers, (c) ranked procurement options, (d) an SPR drawdown schedule. Every number must have an explainable "why."

### 4.2 Data sources to acquire/simulate (be explicit — judges reward this)

| Source | Real option | Hackathon-feasible substitute |
|---|---|---|
| News/policy signals | GDELT Project API (free, geopolitical event data), NewsAPI | GDELT — free and purpose-built for this |
| Shipping/AIS | MarineTraffic API, Spire Maritime (paid) | Use a public sample AIS dataset (Kaggle "AIS vessel traffic") + simulate live updates by replaying it on a timer |
| Sanctions registries | OFAC SDN list (free, US Treasury), UN Security Council sanctions list | Direct download, refresh weekly |
| Commodity prices | EIA (US Energy Information Administration) API, Alpha Vantage for Brent/WTI | EIA API is free and reliable |
| Refinery/port static data | India refinery capacity by PSU reports (IOCL, BPCL, HPCL public data), Strait of Hormuz/Malacca/Suez chokepoint stats (EIA "World Oil Transit Chokepoints") | Compile into a static JSON reference dataset |
| SPR data | PPAC (Petroleum Planning & Analysis Cell, India) public reports | Use most recent public figures, cite as assumption |

### 4.3 Module-by-module ML spec

**M1 — Geopolitical Risk Intelligence Agent**
- Pipeline: scheduled scrape (GDELT + news RSS) → LLM entity/event extraction (event type, location, actors, severity) → map to affected corridor(s) via Knowledge Graph lookup → compute Disruption Probability Score.
- Scoring model: start with a transparent weighted formula (not a black box), e.g.
  `score = w1*event_severity + w2*historical_corridor_volatility + w3*sanctions_delta + w4*price_shock_signal`
  — this is defensible ("explicit, testable assumptions") and can be upgraded to a trained classifier later (label historical events → did disruption occur within N days).
- Output: score 0–100 per corridor/supplier, updated on ingestion, stored in TimescaleDB with full audit trail of contributing signals.

**M2 — Disruption Scenario Modeller**
- Pre-build 3 scenario templates: (1) Hormuz partial closure, (2) OPEC+ emergency cut, (3) Red Sea suspension.
- Each template = a parameterized cascading model: supply volume lost → refinery run-rate impact (by refinery, using known crude-source dependency %) → domestic fuel price pass-through (elasticity assumption, cite source) → power sector stress proxy (diesel/LNG substitution) → GDP impact (use a simple elasticity coefficient from published macro studies, cited).
- Deliverable: every output number must show its formula and source assumption in the UI (a "show your work" panel) — this directly answers the "scenario model fidelity" judging criterion.

**M3 — Adaptive Procurement Orchestrator**
- Build a static+live "alternative supplier" table: supplier country, grade compatibility per Indian refinery, typical spot premium/discount, average shipping time, historical route risk.
- Ranking = MILP optimization (OR-Tools): minimize (cost + risk-adjusted delay) subject to (refinery grade compatibility, tanker availability constraint, volume needed).
- Output: top 3 ranked alternatives with a clear tradeoff table (cost delta, time delta, risk score) — this is the "executability" judges are scoring.

**M4 — Strategic Reserve Optimisation Agent**
- Input: current SPR days-of-cover, forecast supply gap (from M2), replenishment lead time.
- Model: simple dynamic drawdown optimization — minimize risk of stockout while preserving a floor reserve, using linear programming over a rolling horizon.
- Output: recommended daily drawdown rate + trigger conditions to stop/resume.

**M5 — Digital Twin (data layer, frontend renders it)**
- Build the Knowledge Graph: nodes = {wellhead/supplier, tanker, chokepoint/corridor, port, refinery, distribution hub}; edges = routes with live risk-weighted attributes.
- This graph is queried by M1 (which corridors are affected) and M3 (path-finding for alternative routes).

### 4.4 Deliverables from this team
- Data pipeline (Airflow DAGs) with clear source documentation.
- Knowledge graph schema + seed data.
- 4 model/agent services (M1–M4) exposed as internal APIs (see Section 8).
- A written "assumptions ledger" — one page listing every coefficient/elasticity used and its source. **This single document will materially affect your Innovation and Technical Excellence score.**

---

## 5. BACKEND TEAM BRIEF

### 5.1 Mission
Build the orchestration, persistence, and API layer that lets the ML agents talk to each other and to the frontend, reliably and observably.

### 5.2 Services to build

1. **API Gateway / BFF** (FastAPI)
   - Auth (JWT, role-based: Procurement / Policy / Exec viewer)
   - REST endpoints for all read operations (see Section 8 contract)
   - WebSocket channel for live risk score + alert streaming
   - Request aggregation (frontend should rarely need to call more than one endpoint per view)

2. **Agent Orchestrator Service** (Python, LangGraph)
   - Central state machine: listens for new ingestion events → decides which agents to invoke → sequences M1 → M2 → M3 → M4 → writes results → publishes to WebSocket.
   - Must expose a **trace log** per recommendation (which agents ran, what data they used, what they concluded) — feeds the "explainability" panel on frontend and is a strong judging differentiator.

3. **Knowledge Graph Service** (Neo4j + a thin API wrapper)
   - CRUD for graph entities, Cypher queries for path-finding (alternative routes), exposed to M3 and the Digital Twin frontend.

4. **Data Ingestion Service** (Airflow + connectors)
   - Scheduled jobs per source (Section 4.2), normalization, writing into Postgres/TimescaleDB and triggering the Orchestrator on new high-severity events.

5. **Simulation/Scenario Service**
   - Stateless service wrapping M2's scenario templates; accepts a scenario trigger (manual, for the live demo "what-if" button) or an automatic trigger from the Risk Agent.

### 5.3 Database schema (core tables — Postgres/TimescaleDB)

- `corridors` (id, name, geometry, chokepoint_type, baseline_volume)
- `suppliers` (id, country, crude_grade, avg_spot_premium)
- `refineries` (id, name, location, capacity, grade_compatibility[])
- `risk_scores` (corridor_id, supplier_id, score, timestamp, contributing_signals JSONB) — hypertable
- `events` (id, source, raw_text, extracted_entities JSONB, severity, timestamp)
- `scenarios` (id, name, parameters JSONB, results JSONB, run_timestamp)
- `procurement_recommendations` (id, scenario_id, ranked_options JSONB, generated_at)
- `spr_status` (timestamp, days_of_cover, drawdown_rate_recommended)
- `users` (id, role, org)

### 5.4 Non-functional requirements
- Every recommendation must be **reproducible**: store the exact input snapshot used to generate it (for the "explicit, testable assumptions" criterion).
- Target API p95 latency < 500ms for reads; WebSocket push latency < 2s from ingestion to frontend.
- Structured logging across all services (JSON logs) — needed for the demo's "signal-to-recommendation time" metric, which should be computed automatically, not eyeballed.

### 5.5 Deliverables from this team
- Gateway + Orchestrator + Knowledge Graph service + Ingestion service, containerized.
- OpenAPI spec (auto-generated from FastAPI) — hand this to frontend on Day 1.
- A `/metrics/response-time` endpoint that returns the live signal-to-recommendation timing, for the demo.

---

## 6. FRONTEND TEAM BRIEF

### 6.1 Mission
Make the intelligence legible and actionable in seconds. This is a judged **User Experience** category (worth real points) — treat the UI as a product, not a debug console.

### 6.2 Information architecture / screens

1. **War-Room Dashboard (home screen)**
   - Top strip: national risk index (aggregate score), days-of-cover countdown, active alert count.
   - Center: **Digital Twin map** (deck.gl/Mapbox) — India + import corridors (Hormuz, Red Sea/Suez, Malacca) color-coded by live risk score; click a corridor to see contributing signals.
   - Right rail: live alert feed (streaming via WebSocket), most recent first, each alert expandable to show the extraction (event → entities → score impact).

2. **Scenario Simulator**
   - Select a pre-built scenario (Hormuz closure / OPEC+ cut / Red Sea suspension) or adjust parameters (% volume lost, duration).
   - "Run Simulation" → animated cascade: refinery run-rate chart → fuel price chart → power sector stress gauge → GDP impact number, each with a "show assumptions" toggle exposing the formula/source.
   - This is the single highest-leverage screen for **Innovation** and **Technical Excellence** scoring — make the assumptions transparency a first-class UI feature, not a tooltip.

3. **Procurement Console**
   - Table/card view of top-ranked alternative sourcing options (from M3): supplier, route, cost delta, time delta, risk score, grade compatibility check (✓/✗).
   - "Execute" button (mocked for demo — shows a confirmation + generates a procurement order summary PDF/JSON) — this operationalizes "executable recommendations."
   - Comparison view: side-by-side of top 3 options against current baseline.

4. **Strategic Reserve Planner**
   - Days-of-cover gauge, recommended drawdown schedule as a line chart, "what triggers this" explanation panel, manual override slider for policymaker exploration.

5. **Agent Trace / Explainability View** (differentiator — most teams won't build this)
   - Shows the multi-agent chain for any given recommendation: which agent ran, what data it read, what it concluded, timestamped. Builds trust and directly demonstrates "Agentic AI / Multi-Agent Systems" as a judged technology area.

### 6.3 UI flow (happy path for the demo)

```
Landing → War-Room Dashboard (live, ambient)
   → [Alert fires] → click alert → Scenario Simulator auto-populated
      → Run Simulation → cascade animates → 
      → "View Procurement Options" CTA → Procurement Console (pre-ranked)
         → select option → "Execute" → confirmation
      → "View Reserve Impact" CTA → Reserve Planner (updated schedule)
   → Explainability view accessible from any recommendation card ("Why this?")
```

### 6.4 Design direction
- Dark, "operations center" aesthetic (this is a war-room, not a consumer app) — deep navy/graphite background, high-contrast data viz, a single accent color reserved strictly for risk/alert states (e.g., amber→red scale), so risk always reads instantly.
- Typography: a technical/monospace accent font for data readouts (scores, timestamps, coordinates) paired with a clean sans-serif for body text — reinforces the "intelligence platform" feel.
- Motion: use it purposefully — the cascade animation in the Scenario Simulator and live pulse on the map for new alerts are the two places motion should draw the eye; keep everything else static and calm so alerts actually stand out.
- Before final visual polish, the frontend team should consult the `frontend-design` skill guidance available in this environment for concrete component/token choices rather than defaulting to generic dashboard templates.

### 6.5 Deliverables from this team
- All 5 screens, wired to live backend (WebSocket + REST).
- Responsive down to tablet width minimum (judges may view on laptop).
- One polished "cinematic" run-through state for the demo video (Section 9).

---

## 7. DEVOPS / INFRA & INTEGRATION TEAM BRIEF

(If you don't have a dedicated team, backend team owns this — but call it out separately so nothing is dropped.)

- **Containerization:** Docker Compose for local dev with all services (gateway, orchestrator, kg, ingestion, postgres, neo4j, qdrant/pgvector, frontend).
- **Environments:** one shared staging environment reachable via a public URL for judges to click into live (do not rely solely on a video).
- **CI:** basic GitHub Actions — lint + test on PR, build+push images on merge to main.
- **Secrets:** `.env` per service, never committed; use a secrets manager if deploying to cloud.
- **Observability:** centralize logs (even a simple ELK-lite or just structured stdout aggregation) — needed to actually measure and report "signal-to-recommendation time" for the evaluation.
- **Seed/demo data:** a `seed_demo.py` script that pre-loads realistic historical events (2025 US-Iran standoff, recent Red Sea incidents) so the system has a believable state before the live "inject new event" demo moment.

---

## 8. CROSS-TEAM API CONTRACT (freeze this before anyone writes code)

| Endpoint | Method | Owner | Consumed by | Purpose |
|---|---|---|---|---|
| `/api/risk/corridors` | GET | Backend/ML | Frontend map | Current risk score per corridor |
| `/api/risk/events/stream` | WS | Backend | Frontend alert feed | Live event/score push |
| `/api/scenarios` | GET | Backend/ML | Scenario Simulator | List of runnable scenario templates |
| `/api/scenarios/{id}/run` | POST | Backend/ML | Scenario Simulator | Trigger simulation, returns cascade results + assumptions |
| `/api/procurement/recommendations?scenario_id=` | GET | Backend/ML | Procurement Console | Ranked alternative sourcing options |
| `/api/procurement/{id}/execute` | POST | Backend | Procurement Console | Mock-execute a recommendation |
| `/api/reserves/status` | GET | Backend/ML | Reserve Planner | Current days-of-cover + schedule |
| `/api/reserves/simulate` | POST | Backend/ML | Reserve Planner | Manual override scenario |
| `/api/trace/{recommendation_id}` | GET | Backend | Explainability view | Full agent trace for a recommendation |
| `/api/metrics/response-time` | GET | Backend | Demo/judges | Live signal-to-recommendation latency |

All payloads should be JSON with a consistent envelope: `{ data, meta: { generated_at, assumptions_version }, trace_id }` — the `trace_id` ties every response back to the Explainability view.

---

## 9. Sprint Plan & Deliverable Mapping

**Suggested timeline (adapt to your actual hackathon window):**

- **Day 0:** Freeze this document, freeze Section 8 API contract, agree on data sources.
- **Days 1–2:** ML team builds ingestion + risk scoring (M1) with static/replayed data; Backend stands up Gateway + DB schema + mock endpoints (unblocks Frontend immediately); Frontend builds screen shells against mocks.
- **Days 3–4:** Wire real M1 data through; build M2 scenario templates + M3 procurement ranking; Frontend replaces mocks with live calls; Digital Twin map goes live.
- **Day 5:** M4 reserve agent; Explainability/trace view; integration testing end-to-end.
- **Day 6:** Seed realistic demo data, polish UI, record demo video, build architecture diagram, build slide deck.
- **Day 7 (buffer):** Bug fixes, rehearse live demo, fallback recording in case of live-demo risk.

**Deliverable → judging criteria mapping:**

| Deliverable | Innovation | Business Impact | Technical Excellence | Scalability | UX |
|---|---|---|---|---|---|
| Multi-agent orchestration + explainability trace | ✔✔ | | ✔✔ | ✔ | ✔ |
| Explicit assumptions ledger in Scenario Simulator | ✔ | ✔✔ | ✔✔ | | ✔ |
| MILP-optimized procurement ranking | ✔ | ✔✔ | ✔✔ | ✔ | |
| Knowledge graph + geospatial digital twin | ✔✔ | ✔ | ✔ | ✔✔ | ✔✔ |
| Live signal-to-recommendation metric shown on screen | | ✔✔ | ✔ | | ✔ |
| Dockerized, cloud-deployable architecture | | | ✔ | ✔✔ | |
| War-room dashboard design quality | | | | | ✔✔ |

---

## 10. Open Decisions You (CTO) Should Lock Before Kickoff

1. Which LLM provider/model powers the agents (cost vs. capability tradeoff for the hackathon budget).
2. Real API keys to acquire now: GDELT (free, no key needed), EIA API (free key), OFAC list (free download) — get these on Day 0, not Day 3.
3. Whether the live demo will hit a real deployed environment or run locally with a recorded fallback — decide now so DevOps scopes correctly.
4. Final scope cut line if time runs short: **M2 and M4 may ship as rule-based/LP models instead of ML-trained models without hurting the score**, since the rubric explicitly rewards explicit/testable assumptions over model sophistication. Do not cut M1, M3, or M5 — those are the visible spine of the demo.
