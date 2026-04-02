'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import BlobBackground, { PRESET_VIOLET } from '@/components/ui/BlobBackground';
import { getDailyGame } from '../api/client';
import { DailyGameOut } from '../types';
import styles from './MtgDokuOverview.module.css';

const DIFFICULTIES = [
  { key: 'easy',   label: 'Facile',   stars: '★☆☆', description: 'Conditions simples, beaucoup de cartes valides.' },
  { key: 'medium', label: 'Moyen',    stars: '★★☆', description: 'Conditions croisées plus restrictives.' },
  { key: 'hard',   label: 'Difficile',stars: '★★★', description: 'Pour les vrais durs' },
] as const;

export default function MtgDokuOverviewPage() {
  const [game, setGame] = useState<DailyGameOut | null>(null);

  useEffect(() => {
    getDailyGame().then(setGame).catch(() => {});
  }, []);

  function isAvailable(key: 'easy' | 'medium' | 'hard'): boolean {
    return game != null && game[key] != null;
  }

  return (
    <div className={styles.page}>
      <BlobBackground blobs={PRESET_VIOLET} />

      <header className={styles.header}>
        <h1 className={styles.title}>MtgDoku</h1>
        <p className={styles.subtitle}>
          Trouvez une carte Magic qui correspond à chaque intersection de la grille 3×3.
        </p>
        {game && (
          <p className={styles.day}>Grille du {new Date(game.day).toLocaleDateString('fr-FR', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' })}</p>
        )}
      </header>

      <div className={styles.cards}>
        {DIFFICULTIES.map(({ key, label, stars, description }) => {
          const available = isAvailable(key);
          return (
            <Link
              key={key}
              href={available ? `/mtgdoku/${key}` : '#'}
              className={`${styles.card} ${!available ? styles.cardDisabled : ''}`}
              aria-disabled={!available}
            >
              <span className={styles.stars}>{stars}</span>
              <span className={styles.cardLabel}>{label}</span>
              <span className={styles.cardDesc}>{description}</span>
              {!available && game && <span className={styles.unavailable}>Non disponible</span>}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
