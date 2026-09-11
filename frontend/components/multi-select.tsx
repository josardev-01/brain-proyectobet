"use client";

import { useMemo, useState } from "react";

export function MultiSelect({
  label,
  options,
  selected,
  onChange,
  placeholder = "Todas",
}: {
  label: string;
  options: string[];
  selected: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}) {
  const [query, setQuery] = useState("");
  const allOptions = useMemo(
    () => Array.from(new Set([...selected, ...options])).sort((a, b) => a.localeCompare(b, "es")),
    [options, selected],
  );
  const visible = allOptions.filter(option => option.toLocaleLowerCase("es").includes(query.trim().toLocaleLowerCase("es")));

  function toggle(option: string) {
    if (!selected.includes(option) && selected.length >= 100) return;
    onChange(selected.includes(option)
      ? selected.filter(value => value !== option)
      : [...selected, option]);
  }

  return <div className="multi-select-label">
    <span>{label}</span>
    <details className="multi-select">
      <summary>
        <span>{selected.length ? `${selected.length} seleccionada${selected.length === 1 ? "" : "s"}` : placeholder}</span>
        <b aria-hidden="true">⌄</b>
      </summary>
      <div className="multi-select-popover">
        <input aria-label={`Buscar en ${label}`} value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar…" />
        <div className="multi-select-options">
          {visible.length ? visible.map(option => <label className="multi-select-option" key={option}>
            <input
              type="checkbox"
              checked={selected.includes(option)}
              disabled={!selected.includes(option) && selected.length >= 100}
              onChange={() => toggle(option)}
            />
            <span>{option}</span>
          </label>) : <p>Sin coincidencias</p>}
        </div>
        <div className="multi-select-actions">
          {selected.length > 0 && <button className="quiet compact" type="button" onClick={() => onChange([])}>Limpiar selección</button>}
          <button
            className="compact"
            type="button"
            onClick={event => {
              const details = event.currentTarget.closest("details");
              if (details) details.open = false;
            }}
          >Listo</button>
        </div>
      </div>
    </details>
    {selected.length > 0 && <span className="selection-preview">{selected.slice(0, 2).join(" · ")}{selected.length > 2 ? ` · +${selected.length - 2}` : ""}</span>}
  </div>;
}
