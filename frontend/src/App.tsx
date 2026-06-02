import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AdventurePage } from "./pages/AdventurePage";
import { WorldMapPage } from "./pages/WorldMapPage";
import { CollectionPage } from "./pages/CollectionPage";
import { ParentDashboard } from "./pages/ParentDashboard";

function HomePage() {
  return (
    <div className="text-center mt-20">
      <h1 className="text-5xl font-bold text-amber-400 mb-4">数学冒险世界</h1>
      <p className="text-slate-400 mb-8 text-lg">每个孩子专属的、永不结局的数学冒险</p>
      <Link to="/adventure" className="inline-block bg-amber-500 text-black px-10 py-4 rounded-xl font-bold text-xl hover:bg-amber-400 transition-colors">
        开始冒险
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900 text-white">
        <nav className="flex gap-6 p-4 bg-slate-800 border-b border-slate-700 items-center">
          <Link to="/" className="text-amber-400 font-bold text-xl tracking-wide">
            数学冒险世界
          </Link>
          <Link to="/adventure" className="text-slate-300 hover:text-white transition-colors">冒险</Link>
          <Link to="/world" className="text-slate-300 hover:text-white transition-colors">地图</Link>
          <Link to="/collection" className="text-slate-300 hover:text-white transition-colors">收藏</Link>
          <Link to="/parent" className="text-slate-300 hover:text-white transition-colors">家长</Link>
        </nav>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/adventure" element={<AdventurePage />} />
            <Route path="/world" element={<WorldMapPage />} />
            <Route path="/collection" element={<CollectionPage />} />
            <Route path="/parent" element={<ParentDashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
