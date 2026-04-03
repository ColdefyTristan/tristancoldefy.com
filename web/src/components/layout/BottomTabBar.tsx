"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Home, UserRound, LogIn } from "lucide-react";
import styles from "./BottomTabBar.module.css";
import { useAuth } from "../auth/AuthProvider";

function Tab({
  href,
  label,
  children,
}: {
  href: string;
  label: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      className={`${styles.tab} ${isActive ? styles.active : ""}`}
      aria-current={isActive ? "page" : undefined}
    >
      <span className={styles.icon}>{children}</span>
      <span className={styles.label}>{label}</span>
    </Link>
  );
}

export function BottomTabBar() {
  const { user } = useAuth();

  return (
    <nav aria-label="Navigation principale" className={styles.bar}>
      <Tab href="/" label="Accueil">
        <Home size={22} />
      </Tab>
      <Tab href="/riftdle" label="Riftdle">
        <Image src="/images/riftdle_icon.svg" alt="" width={22} height={22} className={styles.riftdleIcon} />
      </Tab>
      <Tab href="/mtgdoku" label="MtgDoku">
        <Image src="/images/mtgdoku_icon.svg" alt="" width={22} height={22} />
      </Tab>
      {user ? (
        <Tab href="/dashboard" label={user.username}>
          <UserRound size={22} />
        </Tab>
      ) : (
        <Tab href="/login" label="Connexion">
          <LogIn size={22} />
        </Tab>
      )}
    </nav>
  );
}
