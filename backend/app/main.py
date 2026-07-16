import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.db.database import engine, Base, SessionLocal
from app.db import models  # noqa: F401 - ensures models are registered on Base
from app.db import user_model  # noqa: F401
from app.db.seed import seed_all
from app.ingestion.event_bus import consume_events
from app.ingestion.simulator import run_autoplay_loop
from app.agents.orchestrator import handle_incoming_event

from app.api.routes import (
    risk_routes, scenario_routes, procurement_routes,
    reserve_routes, system_routes, auth_routes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("sentinel.main")

_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

    consumer_task = asyncio.create_task(consume_events(handle_incoming_event))
    autoplay_task = asyncio.create_task(run_autoplay_loop())
    _background_tasks.extend([consumer_task, autoplay_task])
    logger.info("%s v%s started.", APP_NAME, APP_VERSION)

    yield

    for task in _background_tasks:
        task.cancel()
    logger.info("%s shutting down.", APP_NAME)


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(risk_routes.router)
app.include_router(scenario_routes.router)
app.include_router(procurement_routes.router)
app.include_router(reserve_routes.router)
app.include_router(system_routes.router)


@app.get("/")
def root():
    return {"service": APP_NAME, "version": APP_VERSION, "status": "operational"}


@app.get("/health")
def health():
    return {"status": "ok"}
