import type { TechArticle } from '../types';
import styles from './ArticleCard.module.css';

function Stars({ score }: { score: number }) {
  return (
    <span className={styles.stars} aria-label={`Note ${score} sur 5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < score ? styles.starFilled : styles.starEmpty}>★</span>
      ))}
    </span>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

type ArticleCardProps = {
  article: TechArticle;
};

export function ArticleCard({ article }: ArticleCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.meta}>
        <span className={styles.source}>{article.source}</span>
        {article.published_at && (
          <span className={styles.date}>{formatDate(article.published_at)}</span>
        )}
        {article.interest_score !== null && (
          <Stars score={article.interest_score} />
        )}
      </div>

      <h3 className={styles.title}>
        <a href={article.url} target="_blank" rel="noreferrer">
          {article.title}
        </a>
      </h3>

      {article.summary && (
        <p className={styles.summary}>{article.summary}</p>
      )}

      {article.tags && article.tags.length > 0 && (
        <div className={styles.tags}>
          {article.tags.map((tag) => (
            <span key={tag} className={styles.tag}>{tag}</span>
          ))}
        </div>
      )}
    </article>
  );
}
