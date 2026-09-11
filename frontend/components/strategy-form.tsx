"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Strategy, StrategyCatalog, StrategyMetric } from "@/lib/api";
import { MultiSelect } from "@/components/multi-select";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Logical = "AND" | "OR" | "NOT";
type ConditionDraft = { kind: "condition"; id: string; metric: string; period: "total" | "window"; operator: string; value: string; valueTo: string };
type GroupDraft = { kind: "group"; id: string; logical: Logical; conditions: DraftNode[] };
type DraftNode = ConditionDraft | GroupDraft;
type JsonRecord = Record<string, unknown>;

const defaultAlertFields = ["score", "prematch_odds", "shots_on_target", "corners", "conditions"];

function record(value: unknown): JsonRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as JsonRecord : {};
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.filter(item => typeof item === "string") : [];
}

function typedValue(raw: string, metric?: StrategyMetric) {
  if (metric?.type === "boolean") return raw === "true";
  const number = Number(raw);
  return Number.isNaN(number) ? raw : number;
}

function newCondition(id: string): ConditionDraft {
  return { kind: "condition", id, metric: "minute", period: "total", operator: ">=", value: "45", valueTo: "" };
}

function parseDraft(value: unknown, path = "root"): DraftNode {
  const node = record(value);
  if (typeof node.logical === "string" && Array.isArray(node.conditions)) {
    const logical = (["AND", "OR", "NOT"].includes(node.logical.toUpperCase()) ? node.logical.toUpperCase() : "AND") as Logical;
    const children = node.conditions.map((child, index) => parseDraft(child, `${path}-${index}`));
    return { kind: "group", id: path, logical, conditions: children.length ? children : [newCondition(`${path}-0`)] };
  }
  const configuredMetric = typeof node.metric === "string" ? node.metric : "minute";
  const windowMatch = configuredMetric.match(/^(.*)_last_(5|10|15)$/);
  const values = Array.isArray(node.value) ? node.value : [node.value];
  return {
    kind: "condition",
    id: path,
    metric: windowMatch?.[1] ?? configuredMetric,
    period: windowMatch ? "window" : "total",
    operator: typeof node.operator === "string" ? node.operator : ">=",
    value: values[0] === undefined ? "" : String(values[0]),
    valueTo: values[1] === undefined ? "" : String(values[1]),
  };
}

function initialExpression(template?: Strategy): GroupDraft {
  const parsed = parseDraft(record(template?.config).conditions ?? { logical: "AND", conditions: [{ metric: "minute", operator: ">=", value: 45 }] });
  return parsed.kind === "group" ? parsed : { kind: "group", id: "root", logical: "AND", conditions: [parsed] };
}

function updateNode(node: DraftNode, id: string, updater: (current: DraftNode) => DraftNode): DraftNode {
  if (node.id === id) return updater(node);
  if (node.kind === "group") return { ...node, conditions: node.conditions.map(child => updateNode(child, id, updater)) };
  return node;
}

function removeNode(group: GroupDraft, id: string): GroupDraft {
  return {
    ...group,
    conditions: group.conditions
      .filter(child => child.id !== id)
      .map(child => child.kind === "group" ? removeNode(child, id) : child),
  };
}

function serializeNode(node: DraftNode, windowMinutes: number, metricByValue: Map<string, StrategyMetric>): JsonRecord {
  if (node.kind === "group") {
    return { logical: node.logical, conditions: node.conditions.map(child => serializeNode(child, windowMinutes, metricByValue)) };
  }
  const metric = metricByValue.get(node.metric);
  const value = typedValue(node.value, metric);
  return {
    metric: node.period === "window" ? `${node.metric}_last_${windowMinutes}` : node.metric,
    operator: node.operator,
    value: node.operator === "BETWEEN" ? [value, typedValue(node.valueTo, metric)] : value,
  };
}

export function StrategyForm({ catalog, template, nextVersion }: { catalog: StrategyCatalog; template?: Strategy; nextVersion?: number }) {
  const router = useRouter();
  const templateConfig = record(template?.config);
  const templateScope = record(templateConfig.scope);
  const configuredWindow = Number(templateConfig.feature_window_minutes);
  const [message, setMessage] = useState(template ? `Usando “${template.name}” como base. La versión original no se modificará.` : "");
  const [pending, setPending] = useState(false);
  const [windowMinutes, setWindowMinutes] = useState(catalog.windows.includes(configuredWindow) ? configuredWindow : 10);
  const [expression, setExpression] = useState<GroupDraft>(() => initialExpression(template));
  const [leaguesIncluded, setLeaguesIncluded] = useState(() => list(templateScope.leagues_included));
  const [leaguesExcluded, setLeaguesExcluded] = useState(() => list(templateScope.leagues_excluded));
  const [countriesIncluded, setCountriesIncluded] = useState(() => list(templateScope.countries_included));
  const [alertFields, setAlertFields] = useState(() => {
    const configured = list(templateConfig.alert_fields);
    return configured.length ? configured : defaultAlertFields;
  });
  const metricByValue = useMemo(() => new Map(catalog.metrics.map(metric => [metric.value, metric])), [catalog.metrics]);

  function patchCondition(id: string, patch: Partial<ConditionDraft>) {
    setExpression(current => updateNode(current, id, node => node.kind === "condition" ? { ...node, ...patch } : node) as GroupDraft);
  }

  function changeLogical(id: string, logical: Logical) {
    setExpression(current => updateNode(current, id, node => node.kind === "group"
      ? { ...node, logical, conditions: logical === "NOT" ? node.conditions.slice(0, 1) : node.conditions }
      : node) as GroupDraft);
  }

  function addToGroup(id: string, kind: "condition" | "group") {
    setExpression(current => updateNode(current, id, node => {
      if (node.kind !== "group" || (node.logical === "NOT" && node.conditions.length >= 1)) return node;
      const childId = `${id}-${Date.now()}-${node.conditions.length}`;
      const child = kind === "condition"
        ? newCondition(childId)
        : { kind: "group", id: childId, logical: "AND", conditions: [newCondition(`${childId}-0`)] } as GroupDraft;
      return { ...node, conditions: [...node.conditions, child] };
    }) as GroupDraft);
  }

  function renderNode(node: DraftNode, index: number, depth: number, siblingCount = 1): React.ReactNode {
    if (node.kind === "condition") {
      const selectedMetric = metricByValue.get(node.metric);
      return <div className="condition-row" key={node.id}>
        <span className="condition-index">{index + 1}</span>
        <select aria-label={`Métrica ${node.id}`} value={node.metric} onChange={event => patchCondition(node.id, { metric: event.target.value, period: "total" })}>{catalog.metrics.map(metric => <option key={metric.value} value={metric.value}>{metric.label}</option>)}</select>
        {selectedMetric?.supports_window ? <select aria-label={`Periodo ${node.id}`} value={node.period} onChange={event => patchCondition(node.id, { period: event.target.value as "total" | "window" })}><option value="total">Total del partido</option><option value="window">Últimos {windowMinutes} min</option></select> : <span className="condition-period">Valor actual</span>}
        <select aria-label={`Operador ${node.id}`} value={node.operator} onChange={event => patchCondition(node.id, { operator: event.target.value })}>{catalog.operators.map(operator => <option key={operator}>{operator}</option>)}</select>
        {selectedMetric?.type === "boolean" ? <select aria-label={`Valor ${node.id}`} value={node.value} onChange={event => patchCondition(node.id, { value: event.target.value })}><option value="true">Sí</option><option value="false">No</option></select> : <input aria-label={`Valor ${node.id}`} value={node.value} onChange={event => patchCondition(node.id, { value: event.target.value })} required />}
        {node.operator === "BETWEEN" && <input aria-label={`Valor final ${node.id}`} value={node.valueTo} onChange={event => patchCondition(node.id, { valueTo: event.target.value })} placeholder="hasta" required />}
        <button className="danger compact" type="button" disabled={siblingCount <= 1} onClick={() => setExpression(current => removeNode(current, node.id))}>Quitar</button>
      </div>;
    }
    return <div className={`condition-group ${depth ? "nested" : ""}`} key={node.id}>
      <div className="condition-group-head">
        <label>Combinar<select value={node.logical} onChange={event => changeLogical(node.id, event.target.value as Logical)}><option value="AND">Todas (AND)</option><option value="OR">Cualquiera (OR)</option><option value="NOT">Negar (NOT)</option></select></label>
        {depth > 0 && <button className="danger compact" type="button" disabled={siblingCount <= 1} onClick={() => setExpression(current => removeNode(current, node.id))}>Quitar grupo</button>}
      </div>
      <div className="condition-stack">{node.conditions.map((child, childIndex) => renderNode(child, childIndex, depth + 1, node.conditions.length))}</div>
      <div className="condition-add-actions">
        <button className="quiet add-condition" type="button" disabled={node.logical === "NOT" && node.conditions.length >= 1} onClick={() => addToGroup(node.id, "condition")}>+ Condición</button>
        <button className="quiet add-condition" type="button" disabled={node.logical === "NOT" && node.conditions.length >= 1} onClick={() => addToGroup(node.id, "group")}>+ Grupo AND/OR</button>
      </div>
    </div>;
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
            leagues_included: leaguesIncluded,
            leagues_excluded: leaguesExcluded,
            countries_included: countriesIncluded,
          },
          conditions: serializeNode(expression, windowMinutes, metricByValue),
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
    router.push("/strategies");
    router.refresh();
  }

  return <form className="strategy-form panel" onSubmit={submit}>
    <div className="panel-head"><div><p className="eyebrow">Constructor guiado</p><h2>{template ? "Nueva versión" : "Nueva estrategia"}</h2></div><span className="tag">HEURÍSTICA</span></div>
    <p className="builder-intro">Define el objetivo, limita las competiciones y combina condiciones pre-partido y en vivo. Cada cambio se guarda como una versión nueva.</p>
    <fieldset><legend>1. Identidad y objetivo</legend><div className="form-grid">
      <label>Identificador<input name="strategy_key" defaultValue={template?.strategy_key} placeholder="gol_favorito_presion" pattern="[a-z0-9_]+" required /></label>
      <label>Versión<input name="version" type="number" min="1" defaultValue={nextVersion ?? 1} required /></label>
      <label className="wide">Nombre<input name="name" defaultValue={template ? `${template.name} — nueva versión` : ""} placeholder="Favorito perdiendo con presión" required /></label>
      <label>Evento<select name="objective_type" defaultValue={template?.objective_type}>{catalog.objectives.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      <label>Sujeto<select name="objective_subject" defaultValue={template?.objective_subject}>{catalog.subjects.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      <label>Horizonte objetivo<input name="horizon_minutes" type="number" min="1" max="120" defaultValue={template?.horizon_minutes ?? 10} required /></label>
    </div></fieldset>
    <fieldset><legend>2. Alcance de partidos</legend><div className="form-grid">
      <MultiSelect label="Ligas incluidas" options={catalog.leagues.filter(value => !leaguesExcluded.includes(value))} selected={leaguesIncluded} onChange={values => { setLeaguesIncluded(values); setLeaguesExcluded(current => current.filter(value => !values.includes(value))); }} placeholder="Todas las ligas" />
      <MultiSelect label="Ligas excluidas" options={catalog.leagues.filter(value => !leaguesIncluded.includes(value))} selected={leaguesExcluded} onChange={values => { setLeaguesExcluded(values); setLeaguesIncluded(current => current.filter(value => !values.includes(value))); }} placeholder="Ninguna liga" />
      <MultiSelect label="Países incluidos" options={catalog.countries} selected={countriesIncluded} onChange={setCountriesIncluded} placeholder="Todos los países" />
      <label>Ventana reciente<select value={windowMinutes} onChange={event => setWindowMinutes(Number(event.target.value))}>{catalog.windows.map(value => <option key={value} value={value}>{value} minutos</option>)}</select></label>
    </div></fieldset>
    <fieldset><legend>3. Condiciones y grupos</legend><p className="builder-intro">Agrupa condiciones para representar casos como “local favorito” O “visitante favorito”, conservando todas las condiciones dentro de cada rama.</p>{renderNode(expression, 0, 0)}</fieldset>
    <fieldset><legend>4. Contenido de la alerta</legend><p className="builder-intro">Telegram incluirá únicamente los campos marcados. Si el proveedor no entrega un dato seleccionado, se omite en vez de mostrar N/D.</p><div className="check-grid">{catalog.alert_fields.map(field => <label className="check-option" key={field.value}><input type="checkbox" checked={alertFields.includes(field.value)} onChange={event => setAlertFields(current => event.target.checked ? [...current, field.value] : current.filter(value => value !== field.value))} />{field.label}</label>)}</div></fieldset>
    <div className="form-actions"><p aria-live="polite">{message || "La estrategia se crea inactiva para que puedas revisarla."}</p><button disabled={pending || expression.conditions.length === 0} type="submit">{pending ? "Guardando…" : "Guardar versión"}</button></div>
  </form>;
}
