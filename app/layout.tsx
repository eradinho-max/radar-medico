import type { Metadata, Viewport } from "next";
import "./globals.css";
import ServiceWorkerRegister from "./service-worker-register";

export const metadata: Metadata = {
  title: "Radar Médico — Concursos e Residências",
  description: "Radar gratuito de concursos, processos seletivos e residências médicas.",
  applicationName: "Radar Médico",
  manifest: "/manifest.webmanifest"
};

export const viewport: Viewport = {
  themeColor: "#FFFFFF",
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><ServiceWorkerRegister />{children}</body></html>;
}
