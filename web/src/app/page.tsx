import { Card } from "@/components/layout/Card";
import { InsetBox } from "@/components/ui/InsetBox";
import styles from "./page.module.css"
export default async function CompetencesPage() {

  return (
  <Card variant="medium" background="blob">
    <h1>Bienvenue sur tristancoldefy.com</h1>
    <p>
      Mon espace de projets web, de l’UI au backend. Le site évolue en continu.
    </p>

    <h3>Fonctionalitées :</h3>

    
    <div className={styles.projectRow}>
      <div className={styles.projectRowInner}>
        <span>
          <strong>Riftdle</strong> - Un jeu quotidien inspiré de <a href="https://loldle.net/">LoLdle</a> avec des catégories surprenantes.
        </span>
        <a href="/riftdle">Jouer</a>
      </div>
    </div>
    <div className={styles.projectRow}>
      <div className={styles.projectRowInner}>
        <span>
          <strong>MtgDoku</strong> - Une grille de 9 cartes Magic the Gathering à trouver selon des conditions.
        </span>
        <a href="/mtgdoku">Jouer</a>
      </div>
    </div>
    <div className={styles.projectRow}>
      <div className={styles.projectRowInner}>
        <span>
          <strong>Comptes</strong> - Gestion des comptes, sauvegarde des scores.
        </span>
        <a href="/register">Créer un compte</a>
      </div>
    </div>

    <dl className={styles.techDl}>

  <strong>Technologies utilisées :</strong>

  <div className={styles.row}>
    <dt>
      <strong className={styles.flatText}>FRONTEND</strong>
    </dt>
    <dd>
      <InsetBox>Next.js</InsetBox>
      <InsetBox>TypeScript</InsetBox>
    </dd>
  </div>

  <div className={styles.row}>
    <dt>
      <strong className={styles.flatText}>BACKEND</strong>
    </dt>
    <dd >
      <InsetBox>FastAPI</InsetBox>
      <InsetBox>PostgreSQL</InsetBox>
      <InsetBox>SQLModel</InsetBox>
      <InsetBox>Alembic</InsetBox>
    </dd>
  </div>

  <div className={styles.row}>
    <dt>
      <strong className={styles.flatText}>INFRASTRUCTURE</strong>
    </dt>
    <dd >
      <InsetBox>Docker</InsetBox>
      <InsetBox>Docker Compose</InsetBox>
      <InsetBox>Caddy</InsetBox>
      <InsetBox>AWS Lightsail</InsetBox>
    </dd>
  </div>
</dl>

  <div className={styles.linkFooter}>
    <a href="https://github.com/ColdefyTristan/tristancoldefy.com" target="_blank" rel="noreferrer">Le projet sur Github</a>{" · "}
    <a href="https://hub.docker.com/repository/docker/tristancoldefy/tristancoldefy.com-web/general" target="_blank" rel="noreferrer">Docker Hub (Front)</a>{" · "}
    <a href="https://hub.docker.com/repository/docker/tristancoldefy/tristancoldefy.com-backend" target="_blank" rel="noreferrer">Docker Hub (Back)</a>{" · "}
    <a href="https://www.linkedin.com/in/tristan-coldefy-65670a204/" target="_blank" rel="noreferrer">LinkedIn</a>{" · "}
    <a href="mailto:trcoldefy@gmail.com">trcoldefy@gmail.com</a>
  </div>
  </Card>
    );
} 