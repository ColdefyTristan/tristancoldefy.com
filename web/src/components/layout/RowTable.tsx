"use client";

import styles from "./RowTable.module.css";
import type { ChampRow, Cell } from "@/lib/champData/buildRow"; // adapte le path

function cellClass(c: Cell): string {
  if (c.prox === "equal") return styles.equal;
  if (c.prox === "close") return styles.close;
  return styles.far;
}

function arrow(dir?: "higher" | "lower" | "equal") {
  if (dir === "higher") return "↓";
  if (dir === "lower") return "↑";
  return "";
}


function BucketCell({ cell, value }: { cell: Cell; value: number }) {
  return (
    <td className={cellClass(cell)}>
      <div className={styles.bucketCell}>
        <div className={styles.bucketName}>
          {cell.bucketName ?? "—"}
          <div className={styles.hSep} aria-hidden="true" />
        </div>
        <div className={styles.bucketValue}>
          {value} {arrow(cell.dir)}
        </div>
      </div>
    </td>
  );
}

export default function RowTable({ rows }: { rows: ChampRow[] }) {
  return (
    <div className={styles.root}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Champion</th>
            <th>Couleur</th>
            <th>Nombre de skins</th>
            <th>Jouée par</th>
            <th>Mobilité</th>
            <th>Randomness</th>
            <th>Quantitée de CC</th>
            
          </tr>
        </thead>

        <tbody>
          {
            rows.map((r, i) => (
              <tr key={r.id}>
                <td className={styles.portraitCell}>
                  <img
                    src={r.data.icon_url}
                    alt={r.name}
                    className={styles.portrait}
                    loading="lazy"
                  />
                </td>
                <td className={cellClass(r.cells.mean_hue)}>
                  <div className={styles.hueWidget} aria-label={`Hue ${r.data.mean_hue}`}>
                    <div
                      className={styles.hueCenter}
                      style={{ backgroundColor: r.data.mean_hex }}
                      title={r.data.mean_hex}
                    />
                    <img className={styles.hueRing} src="/images/chroma_circle.png" alt="" />
                    {(() => {
                      const size = 80; // doit matcher le CSS (hueWidget)
                      const cx = size / 2;
                      const cy = size / 2;

                      // rayon du point (au milieu de l’anneau) -> ajuste si besoin
                      const rPoint = 31;

                      // IMPORTANT: ajuste l'offset selon ton image
                      // -90 => hue=0 en haut. Mets 0 si hue=0 doit être à droite.
                      const offsetDeg = -90;
                      const rad = ((r.data.mean_hue + offsetDeg) * Math.PI) / 180;

                      const x = cx + rPoint * Math.cos(rad);
                      const y = cy + rPoint * Math.sin(rad);

                      return (
                        <div
                          className={styles.hueDot}
                          style={{ left: x, top: y }}
                          title={`hue=${r.data.mean_hue}`}
                        />
                      );
                    })()}

                    {(() => {
                      const size = 80;
                      const cx = size / 2;
                      const cy = size / 2;

                      const rArc = 31;         // même “piste” que ton point
                      const sweepDeg = 40;     // longueur d’arc
                      const offsetDeg = -90;   // même offset que ton point

                      const delta = r.cells.mean_hue.delta ?? 0;
                      if (r.cells.mean_hue.prox == "equal") return null; // pas de flèche si equal

                      // direction: delta>0 => valeur "plus haute" => sens trig ? (à ajuster selon ton mapping)
                      const dir = delta < 0 ? 1 : -1; // 1 = sens horaire ou antihoraire selon ton image (voir note)

                      const a0 = r.data.mean_hue + offsetDeg;
                      const a1 = a0 + dir * sweepDeg;

                      const toRad = (deg: number) => (deg * Math.PI) / 180;
                      const polar = (deg: number) => ({
                        x: cx + rArc * Math.cos(toRad(deg)),
                        y: cy + rArc * Math.sin(toRad(deg)),
                      });

                      const p0 = polar(a0);
                      const p1 = polar(a1);

                      // SVG arc flag: large-arc=0 (petit arc), sweep = 1 ou 0
                      const sweepFlag = dir > 0 ? 1 : 0;

                      const d = `M ${p0.x} ${p0.y} A ${rArc} ${rArc} 0 0 ${sweepFlag} ${p1.x} ${p1.y}`;

                      return (
                        <svg className={styles.hueArrow} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
                          <defs>
                            <marker id="arrowHead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                              <path d="M0,0 L6,3 L0,6 Z" fill="black" />
                            </marker>
                          </defs>
                          <path d={d} fill="none" stroke="black" strokeWidth="2" markerEnd="url(#arrowHead)" />
                        </svg>
                      );
                    })()}
                  </div>
                </td>

                <td className={cellClass(r.cells.skin_number)}>{r.data.skin_number} {arrow(r.cells.skin_number.dir)}</td>
                <td className={cellClass(r.cells.family_mastery)}>
                  <div className={styles.family_mastery}>
                    {r.data.family_mastery.length ? r.data.family_mastery.join(", ") : "Personne !"}
                  </div>
                </td>

                <BucketCell cell={r.cells.mobility} value={r.data.mobility} />
                <BucketCell cell={r.cells.randomness} value={r.data.randomness} />
                <BucketCell cell={r.cells.cc_quantity} value={r.data.cc_quantity} />

                
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  );
}
