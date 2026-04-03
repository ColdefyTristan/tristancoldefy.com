import { Github, Linkedin } from "lucide-react";
import Link from "next/link";
import styles from "./Footer.module.css";

export function Footer() {
  return (
    <footer className={styles.footer}>
      <span className={styles.copy}>© {new Date().getFullYear()} Tristan Coldefy</span>
      <div className={styles.links}>
        <Link href="https://github.com/ColdefyTristan" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
          <Github size={16} />
        </Link>
        <Link href="https://www.linkedin.com/in/tristan-coldefy-65670a204/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
          <Linkedin size={16} />
        </Link>
      </div>
    </footer>
  );
}
