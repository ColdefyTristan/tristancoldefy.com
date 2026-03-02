import { TechOverviewHero } from "@/features/techOverview/TechOverviewHero";

export default function ProjetPage() {
  return (
    <main>
      <TechOverviewHero />

      {/* Sections cibles (placeholder) */}
      <section id="frontend"><h2>Frontend</h2></section>
      <section id="backend"><h2>Backend</h2></section>
      <section id="database"><h2>Database</h2></section>
      <section id="infra"><h2>Infrastructure</h2></section>
      <section id="security"><h2>Security</h2></section>
    </main>
  );
}