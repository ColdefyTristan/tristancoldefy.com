import type { HTMLAttributes, ReactNode } from "react";

import styles from "./InsetBox.module.css";

type InsetBoxProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function InsetBox({ children, className = "", ...rest }: InsetBoxProps) {
  return (
    <div className={`${styles.insetBox} ${className}`} {...rest}>
      {children}
    </div>
  );
}