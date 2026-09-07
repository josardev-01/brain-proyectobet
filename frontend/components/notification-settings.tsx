"use client";

import { FormEvent, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Endpoint = { id: number; channel: string; destination: string; label: string; enabled: boolean };

export function NotificationSettings() {
  const [items, setItems] = useState<Endpoint[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const response = await fetch(`${API_URL}/notification-endpoints`, { credentials: "include" });
    if (response.ok) setItems(await response.json());
  }

  useEffect(() => { void load(); }, []);

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API_URL}/notification-endpoints`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel: "telegram", destination: data.get("destination"), label: data.get("label") }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      setMessage(typeof error.detail === "string" ? error.detail : "No se pudo guardar.");
      return;
    }
    event.currentTarget.reset();
    setMessage("Destino guardado.");
    await load();
  }

  async function toggle(item: Endpoint) {
    await fetch(`${API_URL}/notification-endpoints/${item.id}/activation?enabled=${!item.enabled}`, {
      method: "PATCH", credentials: "include",
    });
    await load();
  }

  async function remove(id: number) {
    await fetch(`${API_URL}/notification-endpoints/${id}`, { method: "DELETE", credentials: "include" });
    await load();
  }

  return <section className="panel notification-settings">
    <div className="panel-head"><div><p className="eyebrow">Entregas</p><h2>Telegram</h2></div><span className="tag">BOT GLOBAL</span></div>
    <p className="muted settings-copy">Agrega el chat donde quieres recibir alertas. El token del bot nunca se guarda ni se muestra aquí.</p>
    <form className="form-grid notification-form" onSubmit={add}>
      <label>Etiqueta<input name="label" placeholder="Mi canal principal" /></label>
      <label>Chat ID<input name="destination" placeholder="-1001234567890" pattern="-?[0-9]+" required /></label>
      <button type="submit">Agregar destino</button>
    </form>
    {message && <p className="form-message">{message}</p>}
    <div className="endpoint-list">{items.map(item => <div key={item.id} className="endpoint-row">
      <div><strong>{item.label || "Telegram"}</strong><small>{item.destination}</small></div>
      <span className={`tag ${item.enabled ? "active" : ""}`}>{item.enabled ? "ACTIVO" : "PAUSADO"}</span>
      <button className="quiet" onClick={() => toggle(item)}>{item.enabled ? "Pausar" : "Activar"}</button>
      <button className="danger" onClick={() => remove(item.id)}>Eliminar</button>
    </div>)}</div>
  </section>;
}
