"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui/Button";
import styles from "./page.module.css";

export default function Dashboard() {
  const { user, logout } = useAuth();

  const emailVerified = !!user?.email.primary && !user?.email.pending;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.greeting}>Bonjour, {user?.username}</h1>
      </div>

      {user?.is_family && (
        <div className={styles.familyBanner}>
          <span className={styles.familyIcon}>★</span>
          Vous faites partie de la famille !
        </div>
      )}

      <div className={styles.section}>
        <p className={styles.sectionTitle}>Informations du compte</p>
        <div className={styles.card}>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Nom d'utilisateur</span>
            <span className={styles.infoValue}>{user?.username}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Adresse e-mail</span>
            <span className={styles.infoValue}>{user?.email.primary ?? user?.email.pending ?? "—"}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Statut e-mail</span>
            <span
              className={`${styles.badge} ${emailVerified ? styles.badgeVerified : styles.badgePending}`}
            >
              <span className={styles.dot} />
              {emailVerified ? "Vérifié" : "En attente de vérification"}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => logout()}>
          Se déconnecter
        </Button>
      </div>
    </div>
  );
}
