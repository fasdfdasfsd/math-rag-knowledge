/** Adventure state management with Zustand */

import { create } from "zustand";
import type { AdventureMode, Segment, AnswerResult } from "../types/adventure";
import { api } from "../api/client";

interface AdventureState {
  /** Current adventure session */
  sessionId: string | null;
  mode: AdventureMode | null;
  npc: { id: string; name: string } | null;

  /** 6-segment content (SSE stream accumulates here) */
  segments: Segment[];
  currentSegment: number;

  /** Phase: idle → generating → playing → completed */
  phase: "idle" | "generating" | "playing" | "completed";

  /** Answer state */
  answer: { submitted: boolean; correct: boolean | null; feedback: string } | null;

  /** Error state */
  error: string | null;

  /** Actions */
  startAdventure: (levelId?: string, mode?: string) => Promise<void>;
  submitAnswer: (answer: string, timeSpent: number) => Promise<void>;
  appendSegment: (segment: Segment) => void;
  setPhase: (phase: AdventureState["phase"]) => void;
  reset: () => void;
}

export const useAdventureStore = create<AdventureState>((set, get) => ({
  sessionId: null,
  mode: null,
  npc: null,
  segments: [],
  currentSegment: 0,
  phase: "idle",
  answer: null,
  error: null,

  startAdventure: async (levelId = "l1", mode) => {
    set({ phase: "generating", error: null, segments: [], answer: null });
    try {
      const data = await api.startLevel(levelId, mode);
      set({
        sessionId: data.session_id,
        mode: data.mode as AdventureMode,
        npc: data.npc,
      });
      // Connect to SSE stream via fetch (EventSource can't send auth headers)
      const token = localStorage.getItem("token") || "dev-token";
      const controller = new AbortController();
      (window as unknown as Record<string, unknown>).__adventureAbort = controller;

      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/adventure/levels/${data.session_id}/stream`,
          { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal },
        );
        if (!response.ok) throw new Error(`Stream failed: ${response.status}`);
        const reader = response.body?.getReader();
        if (!reader) throw new Error("No stream body");

        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const segment: Segment = JSON.parse(line.slice(6));
                get().appendSegment(segment);
              } catch { /* skip malformed */ }
            } else if (line.startsWith("event: complete")) {
              set({ phase: "playing" });
            } else if (line.startsWith("event: error")) {
              set({ error: "生成失败，请重试" });
            }
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          set({ error: `连接失败: ${(err as Error).message}` });
        }
      }
    } catch (err) {
      set({ error: (err as Error).message, phase: "idle" });
    }
  },

  submitAnswer: async (answer: string, timeSpent: number) => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const result: AnswerResult = await api.submitAnswer(sessionId, answer, timeSpent);
      set({
        answer: {
          submitted: true,
          correct: result.correct,
          feedback: result.feedback,
        },
      });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  appendSegment: (segment: Segment) => {
    set((s) => ({
      segments: [...s.segments, segment],
      currentSegment: segment.segment,
    }));
  },

  setPhase: (phase) => set({ phase }),

  reset: () => {
    const ctrl = (window as unknown as Record<string, unknown>).__adventureAbort as AbortController | undefined;
    ctrl?.abort();
    set({
      sessionId: null, mode: null, npc: null,
      segments: [], currentSegment: 0,
      phase: "idle", answer: null, error: null,
    });
  },
}));
