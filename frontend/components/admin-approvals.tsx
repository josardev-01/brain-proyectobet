"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type PendingUser = {
  id: number;
  email: string;
  display_name: string;
  approval_status: string;
  created_at: string;
};

export function AdminApprovals() {
  const [users, setUsers] = useState<PendingUser[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const response = await fetch(`${API_URL}/admin/users?approval_status=PENDING`, {
      credentials: "include",
    });
    if (response.ok) setUsers(await response.json());
  }

  useEffect(() => { void load(); }, []);

  async function review(userId: number, approvalStatus: "APPROVED" | "REJECTED") {
    const response = await fetch(`${API_URL}/admin/users/${userId}/approval`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approval_status: approvalStatus }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      setMessage(typeof error.detail === "string" ? error.detail : "No se pudo revisar la cuenta.");
      return;
    }
    setMessage(approvalStatus === "APPROVED" ? "Cuenta aprobada." : "Solicitud rechazada.");
    await load();
  }

  return <section className="panel admin-approvals">
    <div className="panel-head">
      <div><p className="eyebrow">Administración</p><h2>Solicitudes pendientes</h2></div>
      <span className="tag">{users.length} PENDIENTES</span>
    </div>
    {message && <p className="form-message">{message}</p>}
    {users.length === 0
      ? <p className="muted settings-copy">No hay cuentas esperando aprobación.</p>
      : <div className="endpoint-list">{users.map(user => <div key={user.id} className="approval-row">
          <div><strong>{user.display_name}</strong><small>{user.email}</small></div>
          <time>{new Date(user.created_at).toLocaleDateString("es")}</time>
          <button onClick={() => review(user.id, "APPROVED")}>Aprobar</button>
          <button className="danger" onClick={() => review(user.id, "REJECTED")}>Rechazar</button>
        </div>)}</div>}
  </section>;
}
