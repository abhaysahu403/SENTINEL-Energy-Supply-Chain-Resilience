import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Corridor } from "../types";
import { riskColor } from "./ui";

export function CorridorMap({ corridors }: { corridors: Corridor[] }) {
  return (
    <MapContainer
      center={[20, 60]}
      zoom={3}
      scrollWheelZoom={false}
      style={{ height: "100%", width: "100%", background: "var(--color-abyss)" }}
      className="rounded-sm"
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; OpenStreetMap contributors &copy; CARTO'
      />
      {corridors.map((c) => {
        const color = riskColor(c.current_risk_score);
        const radius = 8 + (c.current_risk_score / 100) * 18;
        return (
          <CircleMarker
            key={c.id}
            center={[c.lat, c.lon]}
            radius={radius}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.35, weight: 1.5 }}
          >
            <Tooltip direction="top" offset={[0, -radius]}>
              <div className="font-display text-xs">
                <strong>{c.name}</strong>
                <br />Risk score: {c.current_risk_score.toFixed(1)}
                <br />India dependency: {c.india_dependency_pct}%
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
