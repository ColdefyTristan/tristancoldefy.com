'use client';

import { useState } from 'react';

import type { TagStat,TechArticle } from '../types';
import { ArticleCarousel } from './ArticleCarousel';
import { TagFilter } from './TagFilter';
import styles from './TechWatchSection.module.css';

type Props = {
  articles: TechArticle[];
  tagStats: TagStat[];
};

export function TechWatchSection({ articles, tagStats }: Props) {
  const [activeTag, setActiveTag] = useState<string | null>(null);

  if (articles.length === 0) return null;

  const filtered = activeTag
    ? articles.filter((a) => a.tags?.includes(activeTag))
    : articles;

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Veille de la semaine</h2>
        <span className={styles.subtitle}>{articles.length} article{articles.length > 1 ? 's' : ''} cette semaine</span>
      </div>
      {tagStats.length > 0 && (
        <TagFilter
          tags={tagStats}
          activeTag={activeTag}
          onTagChange={setActiveTag}
          totalCount={articles.length}
        />
      )}
      <div className={styles.carouselBreakout}>
        <ArticleCarousel key={activeTag ?? 'all'} articles={filtered} />
      </div>
    </section>
  );
}
