#!/usr/bin/env bash
# Convenience script: sets up and runs both backend and frontend locally
# (no Docker). Run from the project root: ./scripts/run_local.sh
set -e

cd "$(dirname "$0")/.."

echo "== Setting up backend =="
cd backend
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cd ..

echo "== Setting up frontend =="
cd frontend
npm install
cd ..

echo "== Starting backend on :8000 =="
(cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000) &

echo "== Starting frontend on :5173 =="
(cd frontend && npm run dev) &

echo ""
echo "SENTINEL is starting up:"
echo "  Backend:  http://localhost:8000  (docs at /docs)"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both."
wait
