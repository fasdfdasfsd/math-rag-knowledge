/** API client for math-adventure backend */

import type { AnswerResult, WorldPhase } from "../types/adventure";

const BASE_URL = "http://localhost:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token") || "dev-token";
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ title: "Network Error" }));
    throw new Error(err.title || err.detail || `HTTP ${res.status}`);
  }
  const body = await res.json();
  return body.data ?? body;
}

export const api = {
  /** Start a new adventure level */
  startLevel: (levelId: string, mode?: string) =>
    request<{
      session_id: string; mode: string; difficulty: number;
      status: string; npc: { id: string; name: string };
      primary_kp: { id: string; name: string };
    }>(`/adventure/levels/${levelId}/start`, {
      method: "POST",
      body: JSON.stringify({ level_id: levelId, mode }),
    }),

  /** Submit an answer */
  submitAnswer: (sessionId: string, answer: string, timeSpentMs: number) =>
    request<AnswerResult>(`/adventure/levels/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ level_id: sessionId, answer, time_spent_ms: timeSpentMs }),
    }),

  /** Get world map */
  getWorldMap: () => request<{
    current_phase: string; vehicle: string;
    phases: WorldPhase[];
  }>("/world"),

  /** Get NPC collection */
  getCollection: () => request<{
    total: number; collected: number; items: { npc_id: string; name: string }[];
  }>("/collection"),

  /** Parent dashboard */
  getDashboard: () => request<{
    summary: { total_minutes: number; sessions_completed: number };
    mastery_heatmap: { name: string; mastery: number; status: string }[];
  }>("/parent/dashboard"),
};
