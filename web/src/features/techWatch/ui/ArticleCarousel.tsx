'use client';

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';

import type { TechArticle } from '../types';
import { ArticleCard } from './ArticleCard';
import styles from './ArticleCarousel.module.css';

const GAP = 16;
const AUTO_ADVANCE_MS = 4000;
const CLONES = 3;

type Props = { articles: TechArticle[] };

/** [last N clones] + [real articles] + [first N clones], repeating articles if count < N */
function buildSlides(articles: TechArticle[], n: number): TechArticle[] {
  if (!articles.length) return [];
  const c = articles.length;
  const before = Array.from({ length: n }, (_, i) => articles[((c - n + i) % c + c) % c]);
  const after  = Array.from({ length: n }, (_, i) => articles[i % c]);
  return [...before, ...articles, ...after];
}

function measureEl(el: HTMLElement) {
  const w = el.offsetWidth;
  const cpv = w < 520 ? 1 : 3;
  return { cardWidth: (w - (cpv - 1) * GAP) / cpv, cardsPerView: cpv };
}

export function ArticleCarousel({ articles }: Props) {
  const count   = articles.length;
  const slides  = buildSlides(articles, CLONES);

  // index into slides[]. Real cards live at [CLONES … CLONES+count-1].
  const [index,    setIndex]    = useState(CLONES);
  // jumping=true  → disable slide opacity/transform transitions (avoids flicker on silent jump)
  const [jumping,  setJumping]  = useState(false);
  // animated=true → track has its CSS transition; false = instant move
  const [animated, setAnimated] = useState(true);
  const [paused,   setPaused]   = useState(false);
  const [cardWidth,     setCardWidth]     = useState(0);
  const [cardsPerView,  setCardsPerView]  = useState(3);

  const containerRef = useRef<HTMLDivElement>(null);
  // Ref so the transitionend handler always sees the current index,
  // even if React hasn't re-rendered yet.
  const indexRef    = useRef(CLONES);
  const isJumping   = useRef(false); // prevent auto-advance during silent jump

  // Keep indexRef in sync on every render (safe side-effect in render body)
  indexRef.current = index;

  const offset = index * (cardWidth + GAP);

  function slideClass(i: number): string {
    if (cardsPerView === 1) return i === index ? styles.slideCenter : styles.slideHidden;
    if (i === index)     return styles.slideLeft;
    if (i === index + 1) return styles.slideCenter;
    if (i === index + 2) return styles.slideRight;
    return styles.slideHidden;
  }

  useLayoutEffect(() => {
    if (!containerRef.current) return;
    const { cardWidth: cw, cardsPerView: cpv } = measureEl(containerRef.current);
    setCardWidth(cw);
    setCardsPerView(cpv);
  }, []);

  useEffect(() => {
    const obs = new ResizeObserver(([entry]) => {
      const { cardWidth: cw, cardsPerView: cpv } = measureEl(entry.target as HTMLElement);
      setCardWidth(cw);
      setCardsPerView(cpv);
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  /**
   * Called when the track finishes its CSS transition.
   * If we landed in clone territory, silently teleport to the real equivalent:
   *   • disable track transition  (animated=false  → transition:none on track)
   *   • disable slide transitions  (jumping=true    → .jumping .slide { transition:none })
   *   • set new index              (same visual content, different DOM nodes)
   * All three updates are batched by React 18 into ONE render → no intermediate state.
   * After the browser has painted, re-enable everything.
   */
  const handleTransitionEnd = (e: React.TransitionEvent<HTMLDivElement>) => {
    // Ignore bubbled events from child slides, and non-transform transitions
    if (e.target !== e.currentTarget || e.propertyName !== 'transform') return;

    const i = indexRef.current;
    if (i < CLONES || i >= CLONES + count) {
      const target = i >= CLONES + count ? i - count : i + count;

      isJumping.current = true;

      // Atomic render: track jumps instantly, slides change class without animating
      setIndex(target);
      setJumping(true);
      setAnimated(false);

      // Re-enable transitions once the browser has painted the new position
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          setJumping(false);
          setAnimated(true);
          isJumping.current = false;
        }),
      );
    }
  };

  const advance = useCallback(() => {
    if (isJumping.current) return;
    setIndex((i) => i + 1);
  }, []);

  useEffect(() => {
    if (paused || count <= 1) return;
    const id = setInterval(advance, AUTO_ADVANCE_MS);
    return () => clearInterval(id);
  }, [paused, advance, count]);

  if (count === 0) return <p className={styles.empty}>Aucun article pour ce tag.</p>;

  return (
    <div
      className={styles.wrapper}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div ref={containerRef} className={styles.container}>
        <div
          className={`${styles.track}${jumping ? ` ${styles.jumping}` : ''}`}
          style={{
            transform:  cardWidth > 0 ? `translateX(-${offset}px)` : undefined,
            transition: animated ? undefined : 'none',
          }}
          onTransitionEnd={handleTransitionEnd}
        >
          {slides.map((article, i) => {
            const cls    = slideClass(i);
            const isSide = cls === styles.slideLeft || cls === styles.slideRight;
            return (
              <div
                key={`${i}-${article.id}`}
                className={`${styles.slide} ${cls}`}
                style={{ width: cardWidth > 0 ? cardWidth : undefined }}
                onClick={
                  isSide
                    ? () => {
                        if (isJumping.current) return;
                        setIndex((idx) => (cls === styles.slideLeft ? idx - 1 : idx + 1));
                      }
                    : undefined
                }
              >
                <ArticleCard article={article} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
