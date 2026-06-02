import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api/client";
import type { WorldPhase } from "../types/adventure";

export function WorldMapPage() {
  const [phases, setPhases] = useState<WorldPhase[]>([]);
  const [vehicle, setVehicle] = useState("magic_broom");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getWorldMap().then((data) => {
      setPhases(data.phases);
      setVehicle(data.vehicle ?? "magic_broom");
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const vehicleEmoji: Record<string, string> = {
    magic_broom: "🧹", submarine: "🛳️", spaceship: "🚀", time_machine: "⏰",
  };

  if (loading) {
    return <div className="text-center mt-20 text-slate-400">加载地图中...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <span className="text-4xl">{vehicleEmoji[vehicle] ?? "🧹"}</span>
        <div>
          <h1 className="text-2xl font-bold text-amber-400">冒险地图</h1>
          <p className="text-slate-400">当前载具: {vehicle}</p>
        </div>
      </div>

      <div className="space-y-4">
        {phases.map((phase, i) => (
          <motion.div
            key={phase.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`p-5 rounded-lg border ${
              phase.status === "active"
                ? "bg-slate-800 border-amber-600"
                : phase.status === "completed"
                ? "bg-slate-800 border-green-700"
                : "bg-slate-800/50 border-slate-700 opacity-50"
            }`}
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-white">{phase.name}</h3>
                <p className="text-slate-400 text-sm">
                  {phase.status === "locked" ? "🔒 未解锁" :
                   phase.status === "completed" ? "✅ 已完成" : "📍 探索中"}
                </p>
              </div>
              {phase.status !== "locked" && (
                <div className="text-right">
                  <div className="text-amber-400 font-bold">{Math.round(phase.progress * 100)}%</div>
                  <div className="w-32 h-2 bg-slate-700 rounded-full mt-1">
                    <div
                      className="h-2 bg-amber-400 rounded-full transition-all"
                      style={{ width: `${phase.progress * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
