"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./HeaderNav.module.css";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`${styles.link} ${isActive ? styles.active : ""}`}
      aria-current={isActive ? "page" : undefined}
    >
      {label}
    </Link>
  );
}

export function HeaderNav() {
  return (
    <header className={styles.header}>
      <nav aria-label="Navigation principale" className={styles.nav}>
        <NavLink href="/" label="Accueil" />
        <NavLink href="/login" label="Login" />
        <NavLink href="/playground" label="Playground" />
        <NavLink href="/debug/error" label="Debug Error" />
        <NavLink href="/debug/not-found" label="Debug 404" />
      </nav>
    </header>
  );
}
