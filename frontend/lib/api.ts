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
  owner_id?: number | null;
  config: Record<string, unknown>;
};

export type StrategyMetric = { value: string; label: string; group: string; type: "number" | "boolean" };
export type StrategyCatalog = {
  objectives: { value: string; label: string }[];
  subjects: { value: string; label: string }[];
  operators: string[];
  windows: number[];
  metrics: StrategyMetric[];
  alert_fields: { value: string; label: string }[];
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
  shots_off_target_home: number | null;
  shots_off_target_away: number | null;
  attacks_home: number | null;
  attacks_away: number | null;
  dangerous_attacks_home: number | null;
  dangerous_attacks_away: number | null;
  corners_home: number | null;
  corners_away: number | null;
  possession_home: number | null;
  possession_away: number | null;
  yellow_cards_home: number | null;
  yellow_cards_away: number | null;
  red_cards_home: number | null;
  red_cards_away: number | null;
};

export type StrategyEvaluation = {
  strategy_id: number;
  strategy_key: string;
  strategy_version: number;
  statistical_status: string;
  matched: boolean | null;
  reasons: string[];
  missing_metrics: string[];
  metrics: Record<string, unknown>;
  error: string | null;
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

const API_URL = process.env.API_INTERNAL_URL
  ?? process.env.NEXT_PUBLIC_API_URL
  ?? "http://localhost:8000/api/v1";

export async function apiGet<T>(path: string, fallback: T): Promise<{ data: T; online: boolean }> {
  try {
    const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!response.ok) return { data: fallback, online: false };
    return { data: (await response.json()) as T, online: true };
  } catch {
    return { data: fallback, online: false };
  }
}
