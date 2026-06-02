import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../api/client";

interface CollectedNPC {
  npc_id: string;
  name: string;
  collected_at?: string;
}

export function CollectionPage() {
  const [items, setItems] = useState<CollectedNPC[]>([]);
  const [total, setTotal] = useState(30);
  const [collected, setCollected] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCollection().then((data) => {
      setItems(data.items);
      setTotal(data.total);
      setCollected(data.collected);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center mt-20 text-slate-400">加载收藏中...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-amber-400 mb-2">角色收藏</h1>
      <p className="text-slate-400 mb-6">
        已收集 {collected}/{total} 个 NPC 角色
      </p>

      <div className="w-full h-3 bg-slate-700 rounded-full mb-8">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(collected / total) * 100}%` }}
          className="h-3 bg-amber-400 rounded-full"
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: total }).map((_, i) => {
          const npc = items[i];
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.03 }}
              className={`p-4 rounded-lg text-center border ${
                npc
                  ? "bg-slate-800 border-amber-600 cursor-pointer hover:border-amber-400"
                  : "bg-slate-800/30 border-slate-700 opacity-30"
              }`}
            >
              <div className="text-3xl mb-1">{npc ? "👤" : "❓"}</div>
              <div className="text-sm text-slate-300">{npc?.name ?? "???"}</div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
