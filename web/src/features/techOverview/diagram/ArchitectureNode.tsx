import styles from "./ArchitectureNode.module.css";
import { BrowserPicto } from "./icons/BrowserPicto";
import { useDiagramAnim } from "./timeline/DiagramAnimProvider";

export function ArchitectureNode({
  title,
  href,
  variant,
}: {
  title: string;
  href: string;
  variant?: string;
}) {
  const { state } = useDiagramAnim();

  return (
    <a className={styles.node} href={href} data-variant={variant}>
      <div className={styles.picto} aria-hidden="true">
        {variant === "browser" ? <BrowserPicto anim={state.browser} /> : <div className={styles.pictoPlaceholder} />}
      </div>
      <div className={styles.title}>{title}</div>
    </a>
  );
}