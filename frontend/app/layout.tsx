import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import { Shell } from "@/components/shell";
import "./globals.css";

const body = Manrope({ subsets: ["latin"], variable: "--font-body" });
const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "ProjectBet Intelligence",
  description: "Panel de señales estadísticas de fútbol en vivo",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es"><body className={`${body.variable} ${display.variable}`}><Shell>{children}</Shell></body></html>
  );
}
