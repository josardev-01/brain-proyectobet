import { Empty, PageHeader } from "@/components/shell";
import { apiGet, type Strategy } from "@/lib/api";
import { StrategyForm } from "@/components/strategy-form";

export default async function StrategiesPage() {
  const { data, online } = await apiGet<Strategy[]>("/strategies", []);
  return <><PageHeader eyebrow="Motor dinámico" title="Estrategias" copy="Cada versión conserva su objetivo, configuración y evidencia." online={online} />
    <StrategyForm />
    <section className="card-grid spaced">{data.length ? data.map(item => <article className="strategy-card" key={item.id}>
      <div className="panel-head"><span className={`tag ${item.active ? "active" : ""}`}>{item.active ? "ACTIVA" : "INACTIVA"}</span><b>v{item.version}</b></div>
      <h2>{item.name}</h2><p>{item.objective_subject} · {item.objective_type} en {item.horizon_minutes} min</p>
      <footer><span>{item.statistical_status}</span><code>{item.strategy_key}</code></footer>
    </article>) : <Empty>No hay estrategias sincronizadas.</Empty>}</section></>;
}
