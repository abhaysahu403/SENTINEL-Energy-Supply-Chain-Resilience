"""
Automated tests. Run with: pytest -v (from backend/ with venv active)
Uses a temporary SQLite DB and disables autoplay so tests are deterministic.
"""
import os
os.environ["SENTINEL_AUTOPLAY"] = "0"
os.environ["SENTINEL_DATABASE_URL"] = "sqlite:///./test_sentinel.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
    if os.path.exists("test_sentinel.db"):
        os.remove("test_sentinel.db")


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_corridors_seeded(client):
    resp = client.get("/api/risk/corridors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    ids = {c["id"] for c in data}
    assert "hormuz" in ids


def test_scenario_templates(client):
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    templates = resp.json()
    assert any(t["template_id"] == "hormuz_partial_closure" for t in templates)


def test_run_scenario_produces_explicit_assumptions(client):
    resp = client.post("/api/scenarios/hormuz_partial_closure/run", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "assumptions_used" in data["results"]
    assert data["results"]["volume_lost_mbd"] > 0
    assert data["results"]["volume_lost_mbd"] < data["results"]["total_supply_at_risk_mbd"] + 0.001


def test_procurement_generation(client):
    scn = client.post("/api/scenarios/hormuz_partial_closure/run", json={}).json()
    resp = client.post(f"/api/procurement/generate/{scn['id']}")
    assert resp.status_code == 200
    ranked = resp.json()["ranked_options"]
    assert len(ranked) > 0
    for opt in ranked:
        assert opt["solver_status"] == "Optimal"
        assert opt["sanctions_status"] != "us_sanctioned"


def test_procurement_execute(client):
    scn = client.post("/api/scenarios/opec_emergency_cut/run", json={}).json()
    rec = client.post(f"/api/procurement/generate/{scn['id']}").json()
    resp = client.post(f"/api/procurement/{rec['id']}/execute")
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "confirmed"
    assert order["order_id"].startswith("PO-")


def test_reserve_simulation(client):
    scn = client.post("/api/scenarios/hormuz_partial_closure/run", json={}).json()
    resp = client.post("/api/reserves/simulate", json={"scenario_id": scn["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["schedule"]["solver_status"] == "Optimal"
    assert data["schedule"]["gap_coverage_pct"] <= 100.0


def test_event_injection_triggers_chain(client):
    resp = client.post("/api/events/inject", json={
        "headline": "Test escalation",
        "raw_text": "Test event for automated pipeline validation.",
        "event_type": "military_standoff",
        "affected_corridor": "hormuz",
        "affected_suppliers": ["iraq"],
        "severity": 90,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


def test_auth_register_and_login(client):
    resp = client.post("/api/auth/register", json={
        "email": "test_user@sentinel.example",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "procurement_manager",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "procurement_manager"


def test_metrics_endpoint_shape(client):
    resp = client.get("/api/metrics/response-time")
    assert resp.status_code == 200
    assert "n_traces" in resp.json()
