export type Dashboard = {
  matches: number;
  live_matches: number;
  strategies: number;
  active_strategies: number;
  alerts: number;
  snapshots: number;
  backtest_records: number;
  resolved_alerts: number;
  precision: number | null;
  statistical_status: string;
};

export type Match = {
  id: number;
  provider: string;
  provider_match_id: string;
  kickoff_at: string;
  league_name: string;
  country: string;
  home_team_name: string;
  away_team_name: string;
  favorite_side: "home" | "away";
  favorite_odds: number;
  favorite_probability: number;
  status: string;
  score_home: number | null;
  score_away: number | null;
};

export type Strategy = {
  id: number;
  strategy_key: string;
  version: number;
  name: string;
  statistical_status: string;
  objective_type: string;
  objective_subject: string;
  horizon_minutes: number;
  active: boolean;
};

export type Snapshot = {
  captured_at: string;
  minute: number | null;
  minute_extra: number | null;
  status: string;
  score_home: number | null;
  score_away: number | null;
  shots_home: number | null;
  shots_away: number | null;
  shots_on_target_home: number | null;
  shots_on_target_away: number | null;
  corners_home: number | null;
  corners_away: number | null;
  possession_home: number | null;
  possession_away: number | null;
};

export type Alert = {
  alert_id: string;
  fixture_id: string;
  strategy_key: string;
  strategy_version: number;
  created_at: string;
  minute: number;
  minute_extra: number | null;
  favorite_team_name: string;
  score_favorite: number;
  score_opponent: number;
  delivery_status: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function apiGet<T>(path: string, fallback: T): Promise<{ data: T; online: boolean }> {
  try {
    const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!response.ok) return { data: fallback, online: false };
    return { data: (await response.json()) as T, online: true };
  } catch {
    return { data: fallback, online: false };
  }
}
