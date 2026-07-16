import { useEffect, useRef, useState, useCallback } from "react";
import { WS_BASE } from "../api/client";

export interface LiveMessage {
  type: "risk_update" | "scenario_result" | "procurement_recommendation" | "reserve_update" | "alert";
  payload: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

/**
 * Connects to /ws/live and calls onMessage for every event pushed by the
 * Orchestrator. Auto-reconnects with backoff if the connection drops
 * (e.g. backend restart during development).
 */
export function useLiveFeed(onMessage: (msg: LiveMessage) => void) {
  const [connected, setConnected] = useState(false);
  const retryRef = useRef(1000);
  const wsRef = useRef<WebSocket | null>(null);
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/live`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retryRef.current = 1000;
    };
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as LiveMessage;
        handlerRef.current(msg);
      } catch {
        // ignore malformed frames
      }
    };
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, retryRef.current);
      retryRef.current = Math.min(retryRef.current * 1.5, 15000);
    };
    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { connected };
}
