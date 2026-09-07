import Link from "next/link";
import { PageHeader } from "@/components/shell";
import { apiGet, type Dashboard, type Match } from "@/lib/api";

const emptyDashboard: Dashboard = {
  matches: 0, live_matches: 0, strategies: 0, active_strategies: 0, alerts: 0,
  snapshots: 0, backtest_records: 0, resolved_alerts: 0, precision: null,
  statistical_status: "EXPERIMENTAL",
};

export default async function DashboardPage() {
  const [{ data: dashboard, online }, { data: matches }] = await Promise.all([
    apiGet<Dashboard>("/dashboard", emptyDashboard),
    apiGet<Match[]>("/matches?limit=5", []),
  ]);
  return <>
    <PageHeader eyebrow="Centro de operaciones" title="Señales con contexto, no ruido." copy="Supervisa captura, estrategias y alertas desde una sola vista." online={online} />
    <section className="hero-grid">
      <article className="metric featured"><span>Partidos registrados</span><strong>{dashboard.matches}</strong><small>{dashboard.live_matches} en vivo ahora</small></article>
      <article className="metric"><span>Snapshots</span><strong>{dashboard.snapshots}</strong><small>historia temporal persistida</small></article>
      <article className="metric"><span>Alertas</span><strong>{dashboard.alerts}</strong><small>eventos explicables</small></article>
      <article className="metric"><span>Estrategias activas</span><strong>{dashboard.active_strategies}</strong><small>de {dashboard.strategies} versiones</small></article>
    </section>
    <section className="split">
      <article className="panel">
        <div className="panel-head"><div><p className="eyebrow">Actividad</p><h2>Últimos partidos</h2></div><Link href="/matches">Ver todos →</Link></div>
        <div className="match-list">{matches.length ? matches.map(match => <div className="match-row" key={match.id}>
          <div><strong>{match.home_team_name || "Local"} <span>vs</span> {match.away_team_name || "Visitante"}</strong><small>{match.league_name} · {new Date(match.kickoff_at).toLocaleString("es-PY")}</small></div>
          <div className="score">{match.score_home ?? "–"}<span>:</span>{match.score_away ?? "–"}<small>{match.status}</small></div>
        </div>) : <p className="muted">Sin partidos sincronizados todavía.</p>}</div>
      </article>
      <article className="panel thesis">
        <p className="eyebrow">Estrategia principal</p><h2>Favorito perdiendo + presión</h2>
        <div className="strategy-state"><span>HEURÍSTICA</span><b>v2</b></div>
        <p>Busca un gol del favorito en los próximos 10 minutos usando tiros a puerta, tiros y corners recientes.</p>
        <div className="threshold"><span>Cuota máxima</span><strong>1.55</strong></div>
        <div className="threshold"><span>Activación</span><strong>Min. 45+</strong></div>
        <Link className="button" href="/strategies">Abrir estrategia</Link>
      </article>
    </section>
  </>;
}
