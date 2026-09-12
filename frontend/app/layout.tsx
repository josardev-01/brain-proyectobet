import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProjectBet Intelligence",
  description: "Panel de señales estadísticas de fútbol en vivo",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body><Shell>{children}</Shell></body>
    </html>
  );
}
