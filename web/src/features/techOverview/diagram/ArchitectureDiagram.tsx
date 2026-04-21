"use client";

import { useRef } from "react";

import { infraItems, mainNodes, securityItem } from "./architectureData";
import styles from "./ArchitectureDiagram.module.css";
import { ArchitectureNode } from "./ArchitectureNode";
import { DiagramAnimProvider } from "./timeline/DiagramAnimProvider";

export function ArchitectureDiagram() {
  const rootRef = useRef<HTMLDivElement | null>(null);

  return (
    <div ref={rootRef} className={styles.diagram} aria-label="Project architecture diagram">
      <DiagramAnimProvider observeRef={rootRef}>
        <div className={styles.lane} role="list">
          {mainNodes.map((n, i) => (
            <div key={n.key} className={styles.segment} role="listitem">
              <ArchitectureNode title={n.title} href={n.href} variant={n.variant} />
              {i < mainNodes.length - 1 ? <div className={styles.arrow} aria-hidden="true" /> : null}
            </div>
          ))}
        </div>

        <div className={styles.footnotes}>
          <a className={styles.security} href={securityItem.href}>
            {securityItem.label}
          </a>

          <div className={styles.ribbon} aria-label="Infrastructure notes">
            {infraItems.map((it) => (
              <a key={it.label} className={styles.chip} href={it.href}>
                {it.label}
              </a>
            ))}
          </div>
        </div>
      </DiagramAnimProvider>
    </div>
  );
}