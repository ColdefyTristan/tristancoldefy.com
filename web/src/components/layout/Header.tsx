import Link from "next/link";
import styles from "./Header.module.css";
import {HeaderNav} from "./HeaderNav"
export function Header() {
  return (
    <header className={styles.root}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand}>
          MonSite
        </Link>

        <HeaderNav></HeaderNav>
      </div>
    </header>
  );
}
