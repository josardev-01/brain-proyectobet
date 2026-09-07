"use client";

import { FormEvent, useEffect, useState } from "react";
import { PageHeader } from "@/components/shell";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type User = { email: string; display_name: string };

export default function AccountPage() {
  const [user, setUser] = useState<User | null>(null);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");

  useEffect(() => {
    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then(response => response.ok ? response.json() : Promise.reject())
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("Comprobando…");
    const data = new FormData(event.currentTarget);
    const body: Record<string, string> = {
      email: String(data.get("email")), password: String(data.get("password")),
    };
    if (mode === "register") body.display_name = String(data.get("display_name"));
    const response = await fetch(`${API_URL}/auth/${mode}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      credentials: "include", body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      setMessage(typeof error.detail === "string" ? error.detail : "No se pudo autenticar.");
      return;
    }
    const result = await response.json();
    setUser(result.user);
    setMessage("");
  }

  async function logout() {
    await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
    setUser(null);
  }

  return <>
    <PageHeader eyebrow="Identidad" title="Cuenta" copy="Protege la creación y activación de estrategias." />
    {user ? <section className="panel account-card"><p className="eyebrow">Sesión activa</p><h2>{user.display_name}</h2><p>{user.email}</p><button onClick={logout}>Cerrar sesión</button></section>
      : <form className="panel auth-form" onSubmit={submit}>
        <div className="panel-head"><div><p className="eyebrow">Acceso</p><h2>{mode === "login" ? "Iniciar sesión" : "Crear cuenta"}</h2></div><button className="quiet" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Registrarme" : "Ya tengo cuenta"}</button></div>
        <div className="form-grid auth-fields">
          {mode === "register" && <label>Nombre<input name="display_name" minLength={2} required /></label>}
          <label>Correo<input name="email" type="email" required /></label>
          <label>Contraseña<input name="password" type="password" minLength={10} required /></label>
        </div>
        <div className="form-actions"><p>{message}</p><button type="submit">Continuar</button></div>
      </form>}
  </>;
}
