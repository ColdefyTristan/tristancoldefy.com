import Link from "next/link";

import {BottomTabBar} from "./BottomTabBar";
import styles from "./Header.module.css";
import {HeaderNav} from "./HeaderNav";

export function Header() {
  return (
    <>
      <header className={styles.header}>
        <div className={styles.bg} aria-hidden="true" />
        <div className={styles.inner}>
          <Link href="/" className={styles.brand}>
            TristanColdefy
          </Link>
          <div className={styles.center}>
            <HeaderNav />
          </div>
        </div>
      </header>
      <BottomTabBar />
    </>
  );
}
