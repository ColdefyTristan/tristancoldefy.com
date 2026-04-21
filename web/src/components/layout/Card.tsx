import type { ReactNode } from "react";

import styles from "./Card.module.css";

type CardVariant = "default" | "medium";
type CardBackground = "default" | "blob";

type CardProps = {
  children: ReactNode;
  className?: string;
  variant?: CardVariant;
  background?: CardBackground;
};

export function Card({ children, className = "", variant = "default", background = "default" }: CardProps) {
  return (
    <div className={styles.center}>
      <div className={[styles.card, styles[variant], className].filter(Boolean).join(" ")}>
        {background === "blob" && (
          <div className={styles.bgClip} aria-hidden="true">
            <div className={styles.blob} />
          </div>
        )}
        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}