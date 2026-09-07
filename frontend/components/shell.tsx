import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  ["/", "Resumen"],
  ["/matches", "Partidos"],
  ["/strategies", "Estrategias"],
  ["/alerts", "Alertas"],
  ["/account", "Cuenta"],
];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span className="brand-mark">PB</span>
          <span>ProjectBet<small>Intelligence desk</small></span>
        </Link>
        <nav>{links.map(([href, label]) => <Link key={href} href={href}>{label}</Link>)}</nav>
        <div className="sidebar-foot">
          <span className="pulse" /> Worker de jornada
          <small>Motor preparado para captura en vivo</small>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}

export function PageHeader({ eyebrow, title, copy, online }: {
  eyebrow: string; title: string; copy: string; online?: boolean;
}) {
  return (
    <header className="page-header">
      <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{copy}</p></div>
      {online !== undefined && <span className={`status ${online ? "online" : "offline"}`}>
        {online ? "API conectada" : "API sin conexión"}
      </span>}
    </header>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty"><span>◎</span><p>{children}</p></div>;
}
