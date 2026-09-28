import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./base-structure.css";
import "./premium-visual.css";
import ServiceWorkerRegister from "./service-worker-register";

export const metadata: Metadata = {
  title: "Radar Médico — Concursos e Residências",
  description: "Radar gratuito de concursos, processos seletivos e residências médicas.",
  applicationName: "Radar Médico",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/icone-radar-medico.png",
    shortcut: "/icone-radar-medico.png",
    apple: "/icone-radar-medico.png"
  }
};

export const viewport: Viewport = {
  themeColor: "#FFFFFF",
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><ServiceWorkerRegister />{children}</body></html>;
}
