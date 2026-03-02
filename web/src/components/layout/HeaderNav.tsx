"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./HeaderNav.module.css";
import { useAuth } from "../auth/AuthProvider";
import {LucideIcon ,UserRound} from "lucide-react";



function NavLink({ href, label, icon:Icon }: { href: string; label: string; icon?:LucideIcon }) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`${styles.link} ${isActive ? styles.active : ""}`}
      aria-current={isActive ? "page" : undefined}
    >
      {Icon ? <Icon className={styles.icon} aria-hidden="true" /> : null}
      {label}
    </Link>
  );
}

type NavItem = { href: string; label: string; icon?: LucideIcon };

export function HeaderNav() {
  const { user, status, refreshMe, logout } = useAuth();

  /*const links:NavItem[] = [
    { href: "/parcours", label: "Mon parcours" },
    { href: "/competences", label: "Mes compétences" },
    { href: "/projets", label: "Mes projets" },

  ];*/
  const links:NavItem[] = [
    { href: "/", label:"Accueil"},
    { href: "/familledle", label: "FamilleDLE" },
  ]
  const authLinks:NavItem[] = user
    ? [{ href: "/dashboard", label: user.username , icon: UserRound}] 
    : [
        { href: "/login", label: "Login" },
        { href: "/register", label: "Register" },
      ];

  return (
    <nav aria-label="Navigation principale" className={styles.nav}>
    <div className={styles.group}>
      {links.map((l) => (
        <NavLink key={l.href} {...l} />
      ))}
    </div>
    <span className={styles.vSep} aria-hidden="true" />
    <div className={styles.group}>
      {authLinks.map((l) => (
        <NavLink key={l.href} {...l} />
      ))}
    </div>
  </nav>

  );
}