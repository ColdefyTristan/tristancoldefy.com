import styles from "./TechOverviewHero.module.css";
import { ArchitectureDiagram } from "./diagram/ArchitectureDiagram";

export function TechOverviewHero() {
  return (
    <section className={styles.hero} aria-labelledby="tech-overview-title">
      <div className={styles.inner}>
        <h1 id="tech-overview-title" className={styles.title}>
          Fonctionnement du site
        </h1>

        <ArchitectureDiagram />
      </div>
    </section>
  );
}