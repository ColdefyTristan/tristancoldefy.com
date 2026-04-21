'use client';

import { useState } from 'react';

import type { TagStat } from '../types';
import styles from './TagFilter.module.css';

const VISIBLE_COUNT = 3;

type TagFilterProps = {
  tags: TagStat[];
  activeTag: string | null;
  onTagChange: (tag: string | null) => void;
  totalCount: number;
};

export function TagFilter({ tags, activeTag, onTagChange, totalCount }: TagFilterProps) {
  const [expanded, setExpanded] = useState(false);

  const visibleTags = expanded ? tags : tags.slice(0, VISIBLE_COUNT);
  const hiddenCount = tags.length - VISIBLE_COUNT;

  return (
    <div className={styles.tagFilter} role="group" aria-label="Filtrer par tag">
      <button
        className={`${styles.tag} ${activeTag === null ? styles.active : ''}`}
        onClick={() => onTagChange(null)}
      >
        Tous
        <span className={styles.count}>{totalCount}</span>
      </button>
      {visibleTags.map((t) => (
        <button
          key={t.name}
          className={`${styles.tag} ${activeTag === t.name ? styles.active : ''}`}
          onClick={() => onTagChange(t.name)}
        >
          {t.name}
          <span className={styles.count}>{t.count}</span>
        </button>
      ))}
      {hiddenCount > 0 && (
        <button
          className={styles.more}
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
        >
          {expanded ? '−' : `+${hiddenCount}`}
        </button>
      )}
    </div>
  );
}
