import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface DashboardData {
  summary: {
    total_minutes: number;
    sessions_completed: number;
    streak_days?: number;
    avg_accuracy?: number;
  };
  mastery_heatmap: { name: string; mastery: number; status: string }[];
}

export function ParentDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/parent/dashboard", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token") || "dev-token"}` },
    })
      .then((r) => r.json())
      .then((body) => {
        setData(body.data ?? body);
        setLoading(false);
      })
      .catch(() => {
        // Demo mode
        setData({
          summary: { total_minutes: 185, sessions_completed: 12, streak_days: 5, avg_accuracy: 0.72 },
          mastery_heatmap: [
            { name: "分数比较", mastery: 0.85, status: "green" },
            { name: "分数乘法", mastery: 0.45, status: "yellow" },
            { name: "加法", mastery: 0.95, status: "green" },
            { name: "面积", mastery: 0.30, status: "red" },
          ],
        });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-center mt-20 text-slate-400">加载中...</div>;
  }

  if (!data) return null;

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-amber-400 mb-6">家长仪表盘</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "本周学习", value: `${data.summary.total_minutes} 分钟` },
          { label: "完成关卡", value: `${data.summary.sessions_completed} 关` },
          { label: "连续天数", value: `${data.summary.streak_days ?? 0} 天` },
          { label: "正确率", value: `${Math.round((data.summary.avg_accuracy ?? 0) * 100)}%` },
        ].map((card, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-4 bg-slate-800 rounded-lg border border-slate-700 text-center"
          >
            <div className="text-2xl font-bold text-white">{card.value}</div>
            <div className="text-sm text-slate-400">{card.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Mastery heatmap */}
      <h2 className="text-lg font-bold text-white mb-4">知识点掌握度</h2>
      <div className="space-y-3">
        {data.mastery_heatmap.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-4 p-3 bg-slate-800 rounded-lg"
          >
            <div className="w-24 text-slate-300 text-sm">{item.name}</div>
            <div className="flex-1 h-3 bg-slate-700 rounded-full">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${item.mastery * 100}%` }}
                className={`h-3 rounded-full ${
                  item.status === "green" ? "bg-green-400" :
                  item.status === "yellow" ? "bg-amber-400" : "bg-red-400"
                }`}
              />
            </div>
            <div className="text-slate-400 text-sm w-12 text-right">
              {Math.round(item.mastery * 100)}%
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
