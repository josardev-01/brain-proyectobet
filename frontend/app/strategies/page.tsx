import { Empty, PageHeader } from "@/components/shell";
import { apiGet, type Strategy, type StrategyCatalog } from "@/lib/api";
import { StrategyForm } from "@/components/strategy-form";
import { StrategyActivation } from "@/components/strategy-activation";
import { cookies } from "next/headers";
import Link from "next/link";

export default async function StrategiesPage({ searchParams }: { searchParams: Promise<{ copy?: string }> }) {
  const cookie = (await cookies()).toString();
  const copyId = Number((await searchParams).copy);
  const [{ data, online }, { data: catalog }] = await Promise.all([
    apiGet<Strategy[]>("/strategies", [], cookie),
    apiGet<StrategyCatalog>("/strategy-catalog", { objectives: [], subjects: [], operators: [], windows: [10], metrics: [], alert_fields: [] }),
  ]);
  const template = Number.isInteger(copyId) ? data.find(item => item.id === copyId) : undefined;
  const nextVersion = template
    ? Math.max(...data.filter(item => item.strategy_key === template.strategy_key).map(item => item.version), template.version) + 1
    : 1;
  return <><PageHeader eyebrow="Motor dinámico" title="Estrategias" copy="Cada versión conserva su objetivo, configuración y evidencia." online={online} />
    <StrategyForm key={template?.id ?? "new"} catalog={catalog} template={template} nextVersion={nextVersion} />
    <section className="card-grid spaced">{data.length ? data.map(item => <article className="strategy-card" key={item.id}>
      <div className="panel-head"><span className={`tag ${item.active ? "active" : ""}`}>{item.active ? "ACTIVA" : "INACTIVA"}</span><b>v{item.version}</b></div>
      <h2>{item.name}</h2><p>{item.objective_subject} · {item.objective_type} en {item.horizon_minutes} min</p>
      <footer><span>{item.statistical_status}</span><code>{item.strategy_key}</code></footer><div className="strategy-action"><Link className="quiet-link" href={`/strategies?copy=${item.id}`}>Usar como base</Link></div><StrategyActivation id={item.id} active={item.active} ownerId={item.owner_id ?? null} />
    </article>) : <Empty>No hay estrategias sincronizadas.</Empty>}</section></>;
}
