import { Empty, PageHeader } from "@/components/shell";
import { apiGet, type Alert } from "@/lib/api";

export default async function AlertsPage() {
  const { data, online } = await apiGet<Alert[]>("/alerts?limit=100", []);
  return <><PageHeader eyebrow="Señales" title="Alertas" copy="Triggers deduplicados y listos para entrega." online={online} />
    <section className="alert-stack">{data.length ? data.map(alert => <article className="alert-card" key={alert.alert_id}>
      <div className="alert-minute">{alert.minute}&apos;<small>{alert.minute_extra ? `+${alert.minute_extra}` : ""}</small></div>
      <div><p className="eyebrow">{alert.strategy_key} · v{alert.strategy_version}</p><h2>{alert.favorite_team_name || `Fixture ${alert.fixture_id}`}</h2><p>Favorito bajo presión · marcador {alert.score_favorite}–{alert.score_opponent}</p></div>
      <span className="tag">{alert.delivery_status}</span>
    </article>) : <Empty>Aún no se dispararon alertas.</Empty>}</section></>;
}
