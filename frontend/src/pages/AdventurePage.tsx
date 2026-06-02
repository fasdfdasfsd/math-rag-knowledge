import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdventureStore } from "../stores/adventureStore";

export function AdventurePage() {
  const {
    phase, mode, npc, segments, currentSegment,
    answer, error,
    startAdventure, submitAnswer, reset,
  } = useAdventureStore();

  const [input, setInput] = useState("");
  const [startTime, setStartTime] = useState(0);

  const handleStart = async () => {
    setStartTime(Date.now());
    await startAdventure("l1", "hero");
  };

  const handleSubmit = async () => {
    if (!input.trim()) return;
    const elapsed = Date.now() - startTime;
    await submitAnswer(input.trim(), elapsed);
    setInput("");
  };

  const segmentLabels: Record<number, string> = {
    1: "入口", 2: "到达", 3: "冲突", 4: "解题", 5: "胜利", 6: "钩子",
  };

  return (
    <div className="max-w-2xl mx-auto">
      {phase === "idle" && (
        <div className="text-center mt-20">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleStart}
            className="bg-amber-500 text-black px-10 py-4 rounded-xl font-bold text-xl"
          >
            开启今日冒险
          </motion.button>
        </div>
      )}

      {phase === "generating" && (
        <div className="text-center mt-20">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="text-6xl mb-4"
          >
            🌀
          </motion.div>
          <p className="text-slate-400">传送门正在打开...</p>
          {segments.length > 0 && (
            <p className="text-amber-400 mt-2">
              已到达 {segments.length}/6 段
            </p>
          )}
        </div>
      )}

      {/* Narrative segments (SSE streaming) */}
      <AnimatePresence>
        {segments.map((seg) => (
          <motion.div
            key={seg.segment}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6 p-4 rounded-lg bg-slate-800 border border-slate-700"
          >
            <div className="text-amber-400 text-sm mb-2 font-bold">
              {segmentLabels[seg.segment] || `第${seg.segment}段`}
            </div>
            <div className="text-slate-200 leading-relaxed whitespace-pre-wrap">
              {seg.content}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* NPC info */}
      {npc && (
        <div className="fixed top-20 right-4 bg-slate-800 p-3 rounded-lg border border-amber-600 text-sm">
          <div className="text-amber-400 font-bold">{npc.name}</div>
          <div className="text-slate-400">{mode} 模式</div>
        </div>
      )}

      {/* Answer section */}
      {phase === "playing" && currentSegment >= 4 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 p-4 bg-slate-800 rounded-lg border border-amber-600"
        >
          <label className="block text-slate-300 mb-2">你的答案：</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              className="flex-1 bg-slate-700 text-white px-4 py-2 rounded border border-slate-600 focus:border-amber-400 outline-none"
              placeholder="输入你的答案..."
            />
            <button
              onClick={handleSubmit}
              className="bg-amber-500 text-black px-6 py-2 rounded font-bold hover:bg-amber-400"
            >
              提交
            </button>
          </div>
        </motion.div>
      )}

      {/* Answer feedback */}
      {answer && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mt-4 p-4 rounded-lg ${
            answer.correct ? "bg-green-900 border-green-600" : "bg-amber-900 border-amber-600"
          } border`}
        >
          <div className="font-bold mb-1">
            {answer.correct ? "✨ 太棒了！" : "💪 换个思路试试"}
          </div>
          <div className="text-slate-300">{answer.feedback}</div>
        </motion.div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 p-4 bg-red-900 border border-red-600 rounded-lg text-red-200">
          {error}
          <button onClick={reset} className="ml-4 underline">重试</button>
        </div>
      )}

      {/* Reset button */}
      {phase === "completed" && (
        <div className="text-center mt-8">
          <motion.button
            whileHover={{ scale: 1.05 }}
            onClick={reset}
            className="bg-slate-700 text-slate-300 px-6 py-2 rounded-lg hover:bg-slate-600"
          >
            再来一关
          </motion.button>
        </div>
      )}
    </div>
  );
}
