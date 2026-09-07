"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function StrategyActivation({ id, active, ownerId }: { id: number; active: boolean; ownerId: number | null }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [canManage, setCanManage] = useState(false);
  useEffect(() => {
    if (ownerId === null) return;
    fetch(`${API_URL}/auth/me`, { credentials: "include" })
      .then(response => response.ok ? response.json() : Promise.reject())
      .then(user => setCanManage(user.id === ownerId))
      .catch(() => setCanManage(false));
  }, [ownerId]);
  if (ownerId === null) return <small className="muted">Estrategia del sistema</small>;
  if (!canManage) return null;

  async function toggle() {
    const response = await fetch(`${API_URL}/strategies/${id}/activation?active=${!active}`, {
      method: "PATCH", credentials: "include",
    });
    if (!response.ok) {
      setMessage(response.status === 401 ? "Inicia sesión" : "No se pudo actualizar");
      return;
    }
    router.refresh();
  }

  return <div className="strategy-action"><button className="quiet" onClick={toggle}>{active ? "Desactivar" : "Activar"}</button>{message && <small>{message}</small>}</div>;
}
