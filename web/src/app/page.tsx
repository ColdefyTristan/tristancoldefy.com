import Link from 'next/link';

import { InsetBox } from '@/components/ui/InsetBox';
import { getFeaturedArticles, getTagStats } from '@/features/techWatch/api/client';
import { TechWatchSection } from '@/features/techWatch/ui/TechWatchSection';

import styles from './page.module.css';

export default async function HomePage() {
  const [articles, tagStats] = await Promise.all([
    getFeaturedArticles(20).catch(() => []),
    getTagStats().catch(() => []),
  ]);

  return (
    <div className={styles.page}>
      <div className={styles.bgBlob} aria-hidden="true" />

      <section className={styles.hero}>
        <h1 className={styles.heroTitle}>Tristan Coldefy</h1>
        <p className={styles.heroSub}>Développeur full-stack · Next.js, FastAPI, Docker</p>
        <div className={styles.heroLinks}>
          <a href="https://github.com/ColdefyTristan/tristancoldefy.com" target="_blank" rel="noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/tristan-coldefy-65670a204/" target="_blank" rel="noreferrer">LinkedIn</a>
          <a href="mailto:trcoldefy@gmail.com">trcoldefy@gmail.com</a>
        </div>
      </section>

      <TechWatchSection articles={articles} tagStats={tagStats} />

      <section className={styles.projectsSection}>
        <h2 className={styles.sectionTitle}>Projets</h2>
        <div className={styles.projectRow}>
          <div className={styles.projectRowInner}>
            <span>
              <strong>Riftdle</strong> — Un jeu quotidien inspiré de{' '}
              <a href="https://loldle.net/" target="_blank" rel="noreferrer">LoLdle</a>{' '}
              avec des catégories surprenantes.
            </span>
            <Link href="/riftdle">Jouer</Link>
          </div>
        </div>
        <div className={styles.projectRow}>
          <div className={styles.projectRowInner}>
            <span>
              <strong>MtgDoku</strong> — Une grille de 9 cartes Magic the Gathering à trouver selon des conditions.
            </span>
            <Link href="/mtgdoku">Jouer</Link>
          </div>
        </div>
        <div className={styles.projectRow}>
          <div className={styles.projectRowInner}>
            <span>
              <strong>Comptes</strong> — Gestion des comptes, sauvegarde des scores.
            </span>
            <Link href="/register">Créer un compte</Link>
          </div>
        </div>
        <div className={styles.projectRow}>
          <div className={styles.projectRowInner}>
            <span>
              <strong>Veille techno</strong> — Agrégation RSS automatique via n8n, articles résumés et scorés par IA.
            </span>
          </div>
        </div>
      </section>

      <section className={styles.stackSection}>
        <h2 className={styles.sectionTitle}>Stack</h2>
        <dl className={styles.stackDl}>
          <div className={styles.stackRow}>
            <dt className={styles.stackLabel}>Frontend</dt>
            <dd className={styles.stackItems}>
              <InsetBox>Next.js</InsetBox>
              <InsetBox>TypeScript</InsetBox>
            </dd>
          </div>
          <div className={styles.stackRow}>
            <dt className={styles.stackLabel}>Backend</dt>
            <dd className={styles.stackItems}>
              <InsetBox>FastAPI</InsetBox>
              <InsetBox>PostgreSQL</InsetBox>
              <InsetBox>SQLModel</InsetBox>
              <InsetBox>Alembic</InsetBox>
            </dd>
          </div>
          <div className={styles.stackRow}>
            <dt className={styles.stackLabel}>Infrastructure</dt>
            <dd className={styles.stackItems}>
              <InsetBox>Docker</InsetBox>
              <InsetBox>Caddy</InsetBox>
              <InsetBox>AWS Lightsail</InsetBox>
            </dd>
          </div>
          <div className={styles.stackRow}>
            <dt className={styles.stackLabel}>Automatisation</dt>
            <dd className={styles.stackItems}>
              <InsetBox>n8n</InsetBox>
            </dd>
          </div>
        </dl>
      </section>

      <footer className={styles.linkFooter}>
        <a href="https://hub.docker.com/repository/docker/tristancoldefy/tristancoldefy.com-web/general" target="_blank" rel="noreferrer">Docker Hub (Front)</a>
        {' · '}
        <a href="https://hub.docker.com/repository/docker/tristancoldefy/tristancoldefy.com-backend" target="_blank" rel="noreferrer">Docker Hub (Back)</a>
      </footer>
    </div>
  );
}
