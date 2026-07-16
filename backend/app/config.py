"""
Central configuration for the SENTINEL backend.
All tunable constants live here or in app/agents/assumptions.py so that
every number the system produces can be traced back to an explicit source.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend
PROJECT_ROOT = BASE_DIR.parent                       # .../sentinel
DATA_DIR = PROJECT_ROOT / "data"

DATABASE_URL = os.getenv("SENTINEL_DATABASE_URL", f"sqlite:///{BASE_DIR}/sentinel.db")

# CORS - frontend dev server origins
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# Risk score threshold that auto-triggers the scenario -> procurement -> reserve
# chain in the Orchestrator (see agents/orchestrator.py). Explicit and tunable.
# Calibrated against the current M1 weighting (see agents/assumptions.py):
# a single high-severity event (severity ~90+) with its associated price-shock
# proxy typically scores 45-55 on the 0-100 scale, so 45 is set as the
# trigger point for "this warrants a full response chain," while lower-severity
# routine signals (score < 45) are logged but don't cascade into M2-M4.
RISK_AUTO_TRIGGER_THRESHOLD = 45.0

# Background event simulator: how often (seconds) it may inject a queued
# sample event during a live demo, if the demo/auto-play mode is enabled.
SIMULATOR_INTERVAL_SECONDS = int(os.getenv("SENTINEL_SIM_INTERVAL", "20"))

APP_NAME = "SENTINEL"
APP_VERSION = "0.1.0"
