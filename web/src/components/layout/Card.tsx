import type { ReactNode } from "react";
import styles from "./Card.module.css";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className = "" }: CardProps) {
  return (
    <div className={styles.center}>
      <div className={`${styles.card} ${className}`}>
        <div className={styles.bgClip} aria-hidden="true">
          <div className={styles.blob} />
        </div>

        <div className={styles.content}>
          {children}
        </div>
      </div>
    </div>
  );
}