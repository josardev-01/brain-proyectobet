"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { StrategyCatalog, StrategyMetric } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type ConditionDraft = { id: number; metric: string; period: "total" | "window"; operator: string; value: string; valueTo: string };
const initialConditions: ConditionDraft[] = [
  { id: 1, metric: "minute", period: "total", operator: ">=", value: "45", valueTo: "" },
];

function splitList(value: FormDataEntryValue | null) {
  return String(value ?? "").split(",").map(item => item.trim()).filter(Boolean).slice(0, 100);
}

function typedValue(raw: string, metric?: StrategyMetric) {
  if (metric?.type === "boolean") return raw === "true";
  const number = Number(raw);
  return Number.isNaN(number) ? raw : number;
}

export function StrategyForm({ catalog }: { catalog: StrategyCatalog }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [windowMinutes, setWindowMinutes] = useState(10);
  const [logical, setLogical] = useState("AND");
  const [conditions, setConditions] = useState(initialConditions);
  const [alertFields, setAlertFields] = useState(["score", "prematch_odds", "shots_on_target", "corners"]);
  const metricByValue = useMemo(() => new Map(catalog.metrics.map(metric => [metric.value, metric])), [catalog.metrics]);

  function updateCondition(id: number, patch: Partial<ConditionDraft>) {
    setConditions(current => current.map(item => item.id === id ? { ...item, ...patch } : item));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage("Validando y guardando…");
    const data = new FormData(event.currentTarget);
    const strategyKey = String(data.get("strategy_key"));
    const version = Number(data.get("version"));
    const objectiveType = String(data.get("objective_type"));
    const objectiveSubject = String(data.get("objective_subject"));
    const horizonMinutes = Number(data.get("horizon_minutes"));
    const expression = {
      logical,
      conditions: conditions.map(condition => {
        const metric = metricByValue.get(condition.metric);
        const value = typedValue(condition.value, metric);
        return {
          metric: condition.period === "window"
            ? `${condition.metric}_last_${windowMinutes}`
            : condition.metric,
          operator: condition.operator,
          value: condition.operator === "BETWEEN" ? [value, typedValue(condition.valueTo, metric)] : value,
        };
      }),
    };
    const response = await fetch(`${API_URL}/strategies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
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
          strategy_id: strategyKey, version, status: "HEURÍSTICA", feature_window_minutes: windowMinutes,
          objective: { target: { event_type: objectiveType, subject: objectiveSubject, horizon_minutes: horizonMinutes } },
          scope: {
            leagues_included: splitList(data.get("leagues_included")),
            leagues_excluded: splitList(data.get("leagues_excluded")),
            countries_included: splitList(data.get("countries_included")),
          },
          conditions: expression,
          alert_fields: alertFields,
        },
      }),
    });
    setPending(false);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      setMessage(response.status === 401 ? "Inicia sesión en Cuenta para crear estrategias." : error.detail ?? "No se pudo guardar la estrategia.");
      return;
    }
    setMessage("Versión guardada como heurística inactiva. Puedes revisarla antes de activarla.");
    router.refresh();
  }

  return <form className="strategy-form panel" onSubmit={submit}>
    <div className="panel-head"><div><p className="eyebrow">Constructor guiado</p><h2>Nueva estrategia</h2></div><span className="tag">HEURÍSTICA</span></div>
    <p className="builder-intro">Define el objetivo, limita las competiciones y combina condiciones pre-partido y en vivo. Cada cambio se guarda como una versión nueva.</p>
    <fieldset><legend>1. Identidad y objetivo</legend><div className="form-grid">
      <label>Identificador<input name="strategy_key" placeholder="gol_favorito_presion" pattern="[a-z0-9_]+" required /></label>
      <label>Versión<input name="version" type="number" min="1" defaultValue="1" required /></label>
      <label className="wide">Nombre<input name="name" placeholder="Favorito perdiendo con presión" required /></label>
      <label>Evento<select name="objective_type">{catalog.objectives.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      <label>Sujeto<select name="objective_subject">{catalog.subjects.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      <label>Horizonte objetivo<input name="horizon_minutes" type="number" min="1" max="120" defaultValue="10" required /></label>
    </div></fieldset>
    <fieldset><legend>2. Alcance de partidos</legend><div className="form-grid">
      <label className="wide">Ligas incluidas<input name="leagues_included" placeholder="Premier League, Serie A (vacío = todas)" /></label>
      <label className="wide">Ligas excluidas<input name="leagues_excluded" placeholder="Friendly, Youth League" /></label>
      <label>Países incluidos<input name="countries_included" placeholder="England, Brazil" /></label>
      <label>Ventana reciente<select value={windowMinutes} onChange={event => setWindowMinutes(Number(event.target.value))}>{catalog.windows.map(value => <option key={value} value={value}>{value} minutos</option>)}</select></label>
      <label>Combinar condiciones<select value={logical} onChange={event => setLogical(event.target.value)}><option value="AND">Todas (AND)</option><option value="OR">Cualquiera (OR)</option></select></label>
    </div></fieldset>
    <fieldset><legend>3. Condiciones</legend><div className="condition-stack">
      {conditions.map((condition, index) => {
        const selectedMetric = metricByValue.get(condition.metric);
        return <div className="condition-row" key={condition.id}>
          <span className="condition-index">{index + 1}</span>
          <select aria-label={`Métrica ${index + 1}`} value={condition.metric} onChange={event => updateCondition(condition.id, { metric: event.target.value, period: "total" })}>{catalog.metrics.map(metric => <option key={metric.value} value={metric.value}>{metric.label}</option>)}</select>
          {selectedMetric?.supports_window ? <select aria-label={`Periodo ${index + 1}`} value={condition.period} onChange={event => updateCondition(condition.id, { period: event.target.value as "total" | "window" })}><option value="total">Total del partido</option><option value="window">Últimos {windowMinutes} min</option></select> : <span className="condition-period">Valor actual</span>}
          <select aria-label={`Operador ${index + 1}`} value={condition.operator} onChange={event => updateCondition(condition.id, { operator: event.target.value })}>{catalog.operators.map(operator => <option key={operator}>{operator}</option>)}</select>
          {selectedMetric?.type === "boolean" ? <select aria-label={`Valor ${index + 1}`} value={condition.value} onChange={event => updateCondition(condition.id, { value: event.target.value })}><option value="true">Sí</option><option value="false">No</option></select> : <input aria-label={`Valor ${index + 1}`} value={condition.value} onChange={event => updateCondition(condition.id, { value: event.target.value })} required />}
          {condition.operator === "BETWEEN" && <input aria-label={`Valor final ${index + 1}`} value={condition.valueTo} onChange={event => updateCondition(condition.id, { valueTo: event.target.value })} placeholder="hasta" required />}
          <button className="danger compact" type="button" onClick={() => setConditions(current => current.filter(item => item.id !== condition.id))} disabled={conditions.length === 1}>Quitar</button>
        </div>;
      })}
      <button className="quiet add-condition" type="button" onClick={() => setConditions(current => [...current, { id: Date.now(), metric: "minute", period: "total", operator: ">=", value: "45", valueTo: "" }])}>+ Agregar condición</button>
    </div></fieldset>
    <fieldset><legend>4. Contenido de la alerta</legend><div className="check-grid">{catalog.alert_fields.map(field => <label className="check-option" key={field.value}><input type="checkbox" checked={alertFields.includes(field.value)} onChange={event => setAlertFields(current => event.target.checked ? [...current, field.value] : current.filter(value => value !== field.value))} />{field.label}</label>)}</div></fieldset>
    <div className="form-actions"><p aria-live="polite">{message || "La estrategia se crea inactiva para que puedas revisarla."}</p><button disabled={pending} type="submit">{pending ? "Guardando…" : "Guardar versión"}</button></div>
  </form>;
}
