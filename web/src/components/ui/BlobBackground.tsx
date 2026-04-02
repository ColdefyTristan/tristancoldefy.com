/**
 * BlobBackground — fond décoratif avec des blobs de couleur flous.
 *
 * Usage :
 *   <BlobBackground blobs={PRESET_AURORA} />
 *
 * `color` accepte n'importe quelle valeur CSS background : hex, rgb, hsl,
 * ou un dégradé (radial-gradient, linear-gradient…) pour des effets bicolores.
 */

import styles from './BlobBackground.module.css';

export type Blob = {
  /** Position horizontale depuis le bord gauche (ex: "10%", "400px") */
  x: string;
  /** Position verticale depuis le bord haut (ex: "5%", "200px") */
  y: string;
  /** Diamètre en px */
  size: number;
  /** Couleur ou dégradé CSS — ex: "#7c3aed", "radial-gradient(#0ea5e9, #6d28d9)" */
  color: string;
  /** Rayon de flou en px */
  blur: number;
  /** Opacité 0–1 */
  opacity: number;
};

// ─── Presets couleurs ─────────────────────────────────────────────────────────
// Caractéristiques communes : grande taille, fort blur, opacité très faible.
// Pour changer : remplace le nom du preset dans l'import de MtgDokuPage.tsx.

/** Aurore boréale — bleu-vert froid, dégradé cyan→violet */
export const PRESET_AURORA: Blob[] = [
  { x: '-10%', y: '-15%', size: 1200, color: 'radial-gradient(circle, #06b6d4, #0ea5e9)', blur: 180, opacity: 0.07 },
  { x: '50%',  y: '20%',  size: 1000, color: 'radial-gradient(circle, #10b981, #06b6d4)', blur: 160, opacity: 0.05 },
  { x: '25%',  y: '60%',  size: 800,  color: '#6d28d9',                                   blur: 150, opacity: 0.05 },
];

/** Braise — orange/rouge chaud, contrasté avec un fond froid */
export const PRESET_EMBER: Blob[] = [
  { x: '-5%',  y: '-10%', size: 1100, color: 'radial-gradient(circle, #f5f916a4, #dc2626)', blur: 170, opacity: 0.07 },
  { x: '55%',  y: '30%',  size: 900,  color: '#f59e0b',                                   blur: 160, opacity: 0.05 },
  { x: '10%',  y: '55%',  size: 1000,  color: 'radial-gradient(circle, #9f1239, #7c2d12)', blur: 190, opacity: 0.06 },
];

/** Océan — bleu profond, calme */
export const PRESET_OCEAN: Blob[] = [
  { x: '-8%',  y: '-12%', size: 1300, color: 'radial-gradient(circle, #1d4ed8, #0369a1)', blur: 190, opacity: 0.08 },
  { x: '60%',  y: '45%',  size: 900,  color: '#0e7490',                                   blur: 160, opacity: 0.06 },
];

/** Crépuscule — rose/pêche/mauve, chaleureux */
export const PRESET_DUSK: Blob[] = [
  { x: '-5%',  y: '-10%', size: 1200, color: 'radial-gradient(circle, #ec4899, #f97316)', blur: 180, opacity: 0.07 },
  { x: '55%',  y: '15%',  size: 800,  color: '#a855f7',                                   blur: 150, opacity: 0.06 },
  { x: '20%',  y: '60%',  size: 900,  color: 'radial-gradient(circle, #be185d, #7c3aed)', blur: 160, opacity: 0.05 },
];

/** Forêt — vert émeraude/jade sombre */
export const PRESET_FOREST: Blob[] = [
  { x: '-10%', y: '-8%',  size: 1200, color: 'radial-gradient(circle, #059669, #065f46)', blur: 180, opacity: 0.08 },
  { x: '60%',  y: '40%',  size: 1000, color: '#0d9488',                                   blur: 160, opacity: 0.06 },
  { x: '15%',  y: '65%',  size: 700,  color: '#15803d',                                   blur: 140, opacity: 0.05 },
];

/** Violet — original du thème Arcane, mais adouci */
export const PRESET_VIOLET: Blob[] = [
  { x: '-8%',  y: '-12%', size: 1200, color: 'radial-gradient(circle, #7c3aed, #4338ca)', blur: 190, opacity: 0.07 },
  { x: '55%',  y: '45%',  size: 900,  color: '#a21caf',                                   blur: 160, opacity: 0.05 },
];

// ─────────────────────────────────────────────────────────────────────────────

type BlobBackgroundProps = {
  blobs: Blob[];
};

export default function BlobBackground({ blobs }: BlobBackgroundProps) {
  return (
    <div className={styles.container} aria-hidden="true">
      {blobs.map((blob, i) => (
        <div
          key={i}
          className={styles.blob}
          style={{
            left: blob.x,
            top: blob.y,
            width: blob.size,
            height: blob.size,
            background: blob.color,
            filter: `blur(${blob.blur}px)`,
            opacity: blob.opacity,
          }}
        />
      ))}
    </div>
  );
}
