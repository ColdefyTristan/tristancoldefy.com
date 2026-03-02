import type { DiagramNode } from "./types";

export const mainNodes: DiagramNode[] = [
  { key: "browser", title: "Browser / User", href: "#frontend", variant: "browser" },
  { key: "proxy", title: "Reverse proxy + TLS", href: "#infra" },
  { key: "next", title: "Next.js (Frontend)", href: "#frontend" },
  { key: "api", title: "FastAPI (Backend)", href: "#backend" },
  { key: "db", title: "PostgreSQL (Database)", href: "#database" },
];

export const infraItems = [
  { label: "Docker/Compose", href: "#infra" },
  { label: "Docker Hub", href: "#infra" },
  { label: "AWS Lightsail", href: "#infra" },
  { label: "Porkbun DNS", href: "#infra" },
];

export const securityItem = { label: "Security", href: "#security" };

