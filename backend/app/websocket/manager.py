import json
import logging
from fastapi import WebSocket

logger = logging.getLogger("sentinel.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected (%d active)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected (%d active)", len(self.active_connections))

    async def broadcast(self, event_type: str, payload: dict):
        message = json.dumps({"type": event_type, "payload": payload})
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:  # noqa: BLE001
                stale.append(connection)
        for s in stale:
            self.disconnect(s)


manager = ConnectionManager()
