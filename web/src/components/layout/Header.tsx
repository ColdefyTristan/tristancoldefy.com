import Link from "next/link";
import styles from "./Header.module.css";
import {HeaderNav} from "./HeaderNav"
export function Header() {
  return (
    <header className={styles.header}>
       <div className={styles.bg} aria-hidden="true">
      </div>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand}>
          TristanColdefy
        </Link>
        <div className={styles.center}>
          <HeaderNav></HeaderNav>
        </div>
        
      </div>
    </header>
  );
}
