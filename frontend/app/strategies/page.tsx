import { Empty, PageHeader } from "@/components/shell";
import { apiGet, type Strategy, type StrategyCatalog } from "@/lib/api";
import { StrategyForm } from "@/components/strategy-form";
import { StrategyActivation } from "@/components/strategy-activation";

export default async function StrategiesPage() {
  const [{ data, online }, { data: catalog }] = await Promise.all([
    apiGet<Strategy[]>("/strategies", []),
    apiGet<StrategyCatalog>("/strategy-catalog", { objectives: [], subjects: [], operators: [], windows: [10], metrics: [], alert_fields: [] }),
  ]);
  return <><PageHeader eyebrow="Motor dinámico" title="Estrategias" copy="Cada versión conserva su objetivo, configuración y evidencia." online={online} />
    <StrategyForm catalog={catalog} />
    <section className="card-grid spaced">{data.length ? data.map(item => <article className="strategy-card" key={item.id}>
      <div className="panel-head"><span className={`tag ${item.active ? "active" : ""}`}>{item.active ? "ACTIVA" : "INACTIVA"}</span><b>v{item.version}</b></div>
      <h2>{item.name}</h2><p>{item.objective_subject} · {item.objective_type} en {item.horizon_minutes} min</p>
      <footer><span>{item.statistical_status}</span><code>{item.strategy_key}</code></footer><StrategyActivation id={item.id} active={item.active} ownerId={item.owner_id ?? null} />
    </article>) : <Empty>No hay estrategias sincronizadas.</Empty>}</section></>;
}
