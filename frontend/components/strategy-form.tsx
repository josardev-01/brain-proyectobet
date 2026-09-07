"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function StrategyForm() {
  const router = useRouter();
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("Guardando…");
    const data = new FormData(event.currentTarget);
    const strategyKey = String(data.get("strategy_key"));
    const version = Number(data.get("version"));
    const objectiveType = String(data.get("objective_type"));
    const objectiveSubject = String(data.get("objective_subject"));
    const horizonMinutes = Number(data.get("horizon_minutes"));
    const response = await fetch(`${API_URL}/strategies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        strategy_key: strategyKey,
        version,
        name: String(data.get("name")),
        statistical_status: "HEURÍSTICA",
        objective_type: objectiveType,
        objective_subject: objectiveSubject,
        horizon_minutes: horizonMinutes,
        active: false,
        config: {
          strategy_id: strategyKey,
          version,
          status: "HEURÍSTICA",
          objective: {
            target: { event_type: objectiveType, subject: objectiveSubject, horizon_minutes: horizonMinutes },
          },
          conditions: [],
        },
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      setMessage(error.detail === "esa versión de estrategia ya existe" ? error.detail : "No se pudo guardar. Revisa los campos y la conexión.");
      return;
    }
    event.currentTarget.reset();
    setMessage("Versión creada como heurística inactiva.");
    router.refresh();
  }

  return <form className="strategy-form panel" onSubmit={submit}>
    <div className="panel-head"><div><p className="eyebrow">Nueva definición</p><h2>Crear versión</h2></div><span className="tag">HEURÍSTICA</span></div>
    <div className="form-grid">
      <label>Identificador<input name="strategy_key" placeholder="corner_pressure" pattern="[a-z0-9_]+" required /></label>
      <label>Versión<input name="version" type="number" min="1" defaultValue="1" required /></label>
      <label className="wide">Nombre<input name="name" placeholder="Presión para próximo corner" required /></label>
      <label>Evento<select name="objective_type"><option value="goal">Gol</option><option value="corner">Corner</option><option value="card">Tarjeta</option></select></label>
      <label>Sujeto<select name="objective_subject"><option value="prematch_favorite">Favorito pre-partido</option><option value="home">Local</option><option value="away">Visitante</option><option value="either">Cualquiera</option></select></label>
      <label>Horizonte (min)<input name="horizon_minutes" type="number" min="1" max="120" defaultValue="10" required /></label>
    </div>
    <div className="form-actions"><p>{message}</p><button type="submit">Guardar versión</button></div>
  </form>;
}
