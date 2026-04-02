"use client";

import { useCallback, useRef, useState } from "react";
import styles from "./GameBar.module.css";

export default function GameBar({
  clues,
  selectedIndices,
  cluePoints,
  isFinished,
  onSelect,
}: {
  clues: { label: string; value: string }[];
  selectedIndices?: number[];
  cluePoints?: number;
  isFinished?: boolean;
  onSelect?: (index: number) => void;
}) {
  const [animatingIndex, setAnimatingIndex] = useState<number | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const squareCount = clues.length;
  const selected = selectedIndices ?? [];
  const points = cluePoints ?? 0;
  const available = Array.from({ length: squareCount }, (_, i) => i).filter(
    (i) => !selected.includes(i),
  );
  const btnDisabled = isAnimating || isFinished || points < 3 || available.length === 0;

  const handleClick = useCallback(() => {
    if (isAnimating || available.length === 0) return;

    const finalIndex = available[Math.floor(Math.random() * available.length)];

    const totalCycles = available.length * 2 + Math.floor(Math.random() * available.length) + 2;
    const delays: number[] = [];
    for (let i = 0; i < totalCycles; i++) {
      const progress = i / totalCycles;
      const delay = 40 + Math.pow(progress, 2) * 220;
      delays.push(delay);
    }

    setIsAnimating(true);
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];

    let accumulated = 0;
    let currentPos = 0;

    for (let step = 0; step < totalCycles; step++) {
      const rawIndex = currentPos % available.length;
      const pos = step < totalCycles - 1 ? available[rawIndex] : finalIndex;
      const capturedPos = pos;
      accumulated += delays[step];

      const t = setTimeout(() => {
        setAnimatingIndex(capturedPos);
      }, accumulated);
      timeoutsRef.current.push(t);

      currentPos++;
    }

    const finalT = setTimeout(() => {
      setAnimatingIndex(null);
      setIsAnimating(false);
      onSelect?.(finalIndex);
    }, accumulated + 180);
    timeoutsRef.current.push(finalT);
  }, [isAnimating, available, onSelect]);

  return (
    <div className={styles.bar}>
      {/* Button column */}
      <div className={styles.col}>
        <div className={styles.colHeader}>Obtenir un indice</div>
        <button
          className={`${styles.squareBtn} ${points >= 3 && !isFinished ? styles.squareBtnReady : ""}`}
          onClick={handleClick}
          type="button"
          disabled={btnDisabled}
        >
          <span className={styles.btnContent}>
            <span className={styles.btnLabel}>Coût</span>
            <span className={styles.fraction}>
              <span className={styles.fractionNum}>{points}</span>
              <span className={styles.fractionDen}>3</span>
            </span>
          </span>
        </button>
      </div>

      {/* Square columns */}
      {clues.map((clue, i) => {
        const isSelected = selected.includes(i);
        const isActive = animatingIndex === i;

        return (
          <div key={i} className={styles.col}>
            <div className={styles.colHeader}>{clue.label}</div>
            <div
              className={
                isSelected
                  ? `${styles.square} ${styles.squareSelected}`
                  : isActive
                    ? `${styles.square} ${styles.squareActive}`
                    : styles.square
              }
            >
              {isSelected ? (
                <span className={styles.squareText}>{clue.value}</span>
              ) : (
                <span className={styles.squareMark}>?</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
