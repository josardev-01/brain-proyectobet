import { Empty, PageHeader } from "@/components/shell";
import { apiGet, type Match } from "@/lib/api";
import Link from "next/link";

export default async function MatchesPage() {
  const { data, online } = await apiGet<Match[]>("/matches?limit=100", []);
  return <><PageHeader eyebrow="Observación" title="Partidos" copy="Candidatos pre-partido y su estado más reciente." online={online} />
    <section className="panel table-panel">{data.length ? <table><thead><tr><th>Encuentro</th><th>Liga</th><th>Favorito</th><th>Prob.</th><th>Marcador</th><th>Estado</th></tr></thead><tbody>
      {data.map(match => <tr key={match.id}><td><Link href={`/matches/${match.provider}/${match.provider_match_id}`}><strong>{match.home_team_name || "Local"} — {match.away_team_name || "Visitante"}</strong><small>{new Date(match.kickoff_at).toLocaleString("es-PY")}</small></Link></td><td>{match.league_name}<small>{match.country}</small></td><td>{match.favorite_side === "home" ? "Local" : "Visitante"}<small>@ {match.favorite_odds.toFixed(2)}</small></td><td>{Math.round(match.favorite_probability * 100)}%</td><td>{match.score_home ?? "–"} : {match.score_away ?? "–"}</td><td><span className="tag">{match.status}</span></td></tr>)}
    </tbody></table> : <Empty>Sin partidos en la base. Ejecuta la sincronización inicial.</Empty>}</section></>;
}
