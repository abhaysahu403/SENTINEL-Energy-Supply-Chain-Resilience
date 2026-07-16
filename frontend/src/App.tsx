import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Shell } from "./components/Shell";
import { Dashboard } from "./pages/Dashboard";
import { ScenarioSimulator } from "./pages/ScenarioSimulator";
import { ProcurementConsole } from "./pages/ProcurementConsole";
import { ReservePlanner } from "./pages/ReservePlanner";
import { TraceView } from "./pages/TraceView";
import { useLiveFeed, type LiveMessage } from "./hooks/useLiveFeed";

export default function App() {
  const [lastMessage, setLastMessage] = useState<LiveMessage | null>(null);
  const { connected } = useLiveFeed((msg) => setLastMessage(msg));

  return (
    <BrowserRouter>
      <Shell connected={connected}>
        <Routes>
          <Route path="/" element={<Dashboard lastMessage={lastMessage} />} />
          <Route path="/simulator" element={<ScenarioSimulator />} />
          <Route path="/procurement" element={<ProcurementConsole />} />
          <Route path="/reserves" element={<ReservePlanner />} />
          <Route path="/trace" element={<TraceView />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}
