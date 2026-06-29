import { Link, Route, Routes } from "react-router-dom";

import HistoryPage from "./pages/HistoryPage";
import SubmitClaimPage from "./pages/SubmitClaimPage";

function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <h1 className="text-lg font-semibold text-slate-900">Stacko.Ai</h1>
          <nav className="flex items-center gap-3 text-sm font-medium">
            <Link className="rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" to="/">
              Submit Claim
            </Link>
            <Link className="rounded-md px-3 py-2 text-slate-700 hover:bg-slate-100" to="/history">
              Claims History
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<SubmitClaimPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
