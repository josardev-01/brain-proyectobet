import { PageHeader } from "@/components/shell";
import { apiGet, type Match, type Snapshot } from "@/lib/api";

export default async function MatchDetail({ params }: { params: Promise<{ provider: string; fixtureId: string }> }) {
  const { provider, fixtureId } = await params;
  const [{ data: match, online }, { data: snapshots }] = await Promise.all([
    apiGet<Match | null>(`/matches/${provider}/${fixtureId}`, null),
    apiGet<Snapshot[]>(`/matches/${provider}/${fixtureId}/snapshots`, []),
  ]);
  if (!match) return <><PageHeader eyebrow="Partido" title={`Fixture ${fixtureId}`} copy="No se encontró este partido en la base." online={online} /></>;
  const latest = snapshots.at(-1);
  return <>
    <PageHeader eyebrow={`${match.country} · ${match.league_name}`} title={`${match.home_team_name || "Local"} — ${match.away_team_name || "Visitante"}`} copy={`Favorito ${match.favorite_side === "home" ? "local" : "visitante"} al ${Math.round(match.favorite_probability * 100)}% · cuota ${match.favorite_odds.toFixed(2)}`} online={online} />
    <section className="hero-grid detail-metrics">
      <article className="metric featured"><span>Marcador</span><strong>{latest?.score_home ?? match.score_home ?? "–"} : {latest?.score_away ?? match.score_away ?? "–"}</strong><small>{latest?.minute ? `Minuto ${latest.minute}${latest.minute_extra ? `+${latest.minute_extra}` : ""}` : match.status}</small></article>
      <article className="metric"><span>Tiros a puerta</span><strong>{latest?.shots_on_target_home ?? "–"} : {latest?.shots_on_target_away ?? "–"}</strong><small>acumulado observado</small></article>
      <article className="metric"><span>Tiros</span><strong>{latest?.shots_home ?? "–"} : {latest?.shots_away ?? "–"}</strong><small>acumulado observado</small></article>
      <article className="metric"><span>Corners</span><strong>{latest?.corners_home ?? "–"} : {latest?.corners_away ?? "–"}</strong><small>acumulado observado</small></article>
    </section>
    <section className="panel timeline"><div className="panel-head"><div><p className="eyebrow">Historia</p><h2>Snapshots disponibles</h2></div><b>{snapshots.length}</b></div>
      {snapshots.map((snapshot, index) => <div className="timeline-row" key={`${snapshot.captured_at}-${index}`}><span>{snapshot.minute ?? "–"}&apos;</span><div><b>{snapshot.score_home ?? "–"} : {snapshot.score_away ?? "–"}</b><small>SOT {snapshot.shots_on_target_home ?? "–"}:{snapshot.shots_on_target_away ?? "–"} · tiros {snapshot.shots_home ?? "–"}:{snapshot.shots_away ?? "–"} · corners {snapshot.corners_home ?? "–"}:{snapshot.corners_away ?? "–"}</small></div><time>{new Date(snapshot.captured_at).toLocaleTimeString("es-PY")}</time></div>)}
    </section>
  </>;
}
