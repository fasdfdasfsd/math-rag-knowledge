/** Adventure types matching backend API contracts */

export type AdventureMode = "hero" | "mentor" | "explore";

export interface Segment {
  segment: number;
  content: string;
  is_last: boolean;
  finish_reason: string | null;
}

export interface LevelStartResponse {
  session_id: string;
  mode: AdventureMode;
  difficulty: number;
  primary_kp: { id: string; name: string };
  npc: { id: string; name: string };
  status: string;
}

export interface AnswerResult {
  correct: boolean;
  feedback: string;
  next_action: "continue" | "hint" | "segment_5";
}

export interface WorldMapData {
  current_phase: string;
  phases: WorldPhase[];
  vehicle: string;
}

export interface WorldPhase {
  id: string;
  name: string;
  status: "locked" | "active" | "completed";
  progress: number;
}
