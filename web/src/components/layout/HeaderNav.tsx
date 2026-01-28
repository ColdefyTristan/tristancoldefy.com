"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./HeaderNav.module.css";
import { useAuth } from "../auth/AuthProvider";
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
  const { user, status, refreshMe, logout } = useAuth();

  const links = [
    { href: "/", label: "Accueil" },
    { href: "/playground", label: "Playground" },
    { href: "/debug/error", label: "Debug Error" },
    { href: "/debug/not-found", label: "Debug 404" },
  ];

  const authLinks = user
    ? [{ href: "/dashboard", label: user.username }] // ou un bouton menu
    : [
        { href: "/login", label: "Login" },
        { href: "/register", label: "Register" },
      ];

  return (
    <header className={styles.header}>
      <nav aria-label="Navigation principale" className={styles.nav}>
        {[...links, ...authLinks].map((l) => (
          <NavLink key={l.href} href={l.href} label={l.label} />
        ))}
      </nav>
    </header>
  );
}