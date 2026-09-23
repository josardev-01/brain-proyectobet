"use client";

import { useState } from "react";
import type { Match, StrategyPreview as PreviewResult } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function StrategyPreview({ strategyId, matches }: { strategyId: number; matches: Match[] }) {
  const available = matches.filter(match => match.last_snapshot_at);
  const [matchId, setMatchId] = useState(String(available[0]?.id ?? ""));
  const [result, setResult] = useState<PreviewResult | null>(null);
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);

  async function preview() {
    if (!matchId) return;
    setPending(true);
    setMessage("");
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/strategies/${strategyId}/preview?match_id=${matchId}`, {
        credentials: "include",
        cache: "no-store",
      });
      if (!response.ok) {
        setMessage(response.status === 401 ? "Inicia sesión para probar la estrategia." : "No se pudo evaluar este partido.");
      } else {
        setResult(await response.json() as PreviewResult);
      }
    } catch {
      setMessage("No se pudo conectar con la API.");
    } finally {
      setPending(false);
    }
  }

  return <div className="strategy-preview">
    <label>Probar en partido registrado
      <select value={matchId} onChange={event => { setMatchId(event.target.value); setResult(null); }} disabled={!available.length}>
        {available.map(match => <option key={match.id} value={match.id}>{match.home_team_name} vs {match.away_team_name} · {match.league_name}</option>)}
      </select>
    </label>
    <button type="button" className="quiet" disabled={!matchId || pending} onClick={preview}>{pending ? "Evaluando…" : "Probar estrategia"}</button>
    {!available.length && <small>Necesitas al menos un partido con capturas.</small>}
    {message && <small role="status">{message}</small>}
    {result && <div className="preview-result" role="status">
      <strong>{result.matched === null ? "No se pudo evaluar" : result.matched ? "Coincide con las condiciones" : "No coincide con las condiciones"}</strong>
      <small>{result.snapshot_count} capturas · {result.observation_state === "LIVE" ? "Datos recientes" : "Evaluación sobre datos históricos o desactualizados"}</small>
      {result.captured_at && <small>Última captura: {new Date(result.captured_at).toLocaleString("es-PY")}</small>}
      {result.error && <small>{result.error}</small>}
      {result.missing_metrics.length > 0 && <small>Faltan datos: {result.missing_metrics.join(", ")}</small>}
      {result.reasons.length > 0 && <small>Evaluación: {result.reasons.join(" · ")}</small>}
      <small>Esta prueba no envía alertas ni valida la probabilidad del objetivo.</small>
    </div>}
  </div>;
}
