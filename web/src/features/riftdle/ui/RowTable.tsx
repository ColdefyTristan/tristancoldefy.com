"use client";

import styles from "./RowTable.module.css";
import type { ChampRow, Cell, RowColumn } from "../types";

// --------------------
// Column config
// --------------------

const COLUMN_HEADERS: Record<RowColumn, string> = {
  skin_number:    "Nombre de skins",
  family_mastery: "Joué par",
  colorwheel:     "Couleur",
  mobility:       "Mobilité",
  randomness:     "Randomness",
  cc_quantity:    "Quantité de CC",
  intension:      "Intension",
  vote:           "Vote",
  regime:         "Régime",
  pilosite:       "Pilosité",
  genre:          "Genre",
  ressource:      "Ressource",
  portee:         "Portée",
  annee_sortie:   "Année",
  role:           "Position",
  espece:         "Espèce",
  region:         "Région",
};

// --------------------
// Helpers
// --------------------

function cellClass(c: Cell): string {
  if (c.prox === "equal") return styles.equal;
  if (c.prox === "close") return styles.close;
  return styles.far;
}


function ListCell({ cell, values }: { cell: Cell; values: string[] }) {
  return (
    <td className={cellClass(cell)}>
      <div className={styles.listCell}>
        {values.length ? values.join(", ") : "—"}
      </div>
    </td>
  );
}

// --------------------
// Sub-components
// --------------------

function BucketCell({ cell }: { cell: Cell; rank?: number; total?: number }) {
  // Contenu conservé pour usage futur :
  // <div className={styles.bucketCell}>
  //   <div className={styles.bucketName}>
  //     {cell.bucketName ?? "—"}
  //     <div className={styles.hSep} aria-hidden="true" />
  //   </div>
  //   <div className={styles.bucketValue}>
  //     <span className={styles.fraction}>
  //       <span className={styles.fractionNum}>{rank ?? "?"}</span>
  //       <span className={styles.fractionDen}>{total ?? "?"}</span>
  //     </span>
  //     {cmp(cell.dir)} {"?"}
  //   </div>
  // </div>
  return <td className={cellClass(cell)}><div className={styles.bucketText} >{cell.bucketName ?? "—"}</div></td>;
}

const SIZE = 80;
const CX = SIZE / 2;
const CY = SIZE / 2;
const R = 31;
const OFFSET_DEG = -90;

function hueDotStyle(hue: number): React.CSSProperties {
  const rad = ((hue + OFFSET_DEG) * Math.PI) / 180;
  return {
    left: `${((CX + R * Math.cos(rad)) / SIZE) * 100}%`,
    top: `${((CY + R * Math.sin(rad)) / SIZE) * 100}%`,
  };
}

function HueArc({ hue, delta }: { hue: number; delta: number }) {
  const SWEEP_DEG = 40;
  const dir = delta < 0 ? 1 : -1;
  const a0 = hue + OFFSET_DEG;
  const a1 = a0 + dir * SWEEP_DEG;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const polar = (deg: number) => ({
    x: CX + R * Math.cos(toRad(deg)),
    y: CY + R * Math.sin(toRad(deg)),
  });
  const p0 = polar(a0);
  const p1 = polar(a1);
  const sweepFlag = dir > 0 ? 1 : 0;
  const d = `M ${p0.x} ${p0.y} A ${R} ${R} 0 0 ${sweepFlag} ${p1.x} ${p1.y}`;

  return (
    <svg className={styles.hueArrow} viewBox={`0 0 ${SIZE} ${SIZE}`} aria-hidden="true">
      <defs>
        <marker id="hueArrowHead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="black" />
        </marker>
      </defs>
      <path d={d} fill="none" stroke="black" strokeWidth="2" markerEnd="url(#hueArrowHead)" />
    </svg>
  );
}

function HueCell({ row }: { row: ChampRow }) {
  const cell = row.cells.mean_hue;
  const hue = row.data.mean_hue;
  const delta = cell.delta ?? 0;

  return (
    <td className={cellClass(cell)}>
      <div className={styles.hueWidget} aria-label={`Hue ${hue}`}>
        <div
          className={styles.hueCenter}
          style={{ backgroundColor: row.data.mean_hex }}
          title={row.data.mean_hex}
        />
        <img className={styles.hueRing} src="/images/chroma_circle.png" alt="" />
        <div className={styles.hueDot} style={hueDotStyle(hue)} title={`hue=${hue}`} />
        {cell.prox !== "equal" && <HueArc hue={hue} delta={delta} />}
      </div>
    </td>
  );
}

function renderCell(row: ChampRow, col: RowColumn): React.ReactNode {
  switch (col) {
    case "skin_number":
      return (
        <td key={col} className={cellClass(row.cells.skin_number)}>
          {row.data.skin_number}
        </td>
      );
    case "colorwheel":
      return <HueCell key={col} row={row} />;
    case "family_mastery":
      return <ListCell key={col} cell={row.cells.family_mastery} values={row.data.family_mastery} />;
    case "vote":
      return <ListCell key={col} cell={row.cells.vote} values={row.data.vote} />;
    case "regime":
      return <ListCell key={col} cell={row.cells.regime} values={row.data.regime} />;
    case "pilosite":
      return <ListCell key={col} cell={row.cells.pilosite} values={row.data.pilosite} />;
    case "mobility":
      return (
        <BucketCell
          key={col}
          cell={row.cells.mobility}
          rank={row.data.mobility_rank}
          total={row.data.total_champions}
        />
      );
    case "randomness":
      return (
        <BucketCell
          key={col}
          cell={row.cells.randomness}
          rank={row.data.randomness_rank}
          total={row.data.total_champions}
        />
      );
    case "cc_quantity":
      return (
        <BucketCell
          key={col}
          cell={row.cells.cc_quantity}
          rank={row.data.cc_quantity_rank}
          total={row.data.total_champions}
        />
      );
    case "intension":
      return (
        <BucketCell
          key={col}
          cell={row.cells.intension}
          rank={row.data.intension_rank}
          total={row.data.total_champions}
        />
      );
  }
}

// --------------------
// Main component
// --------------------

export default function RowTable({
  rows,
  activeColumns,
}: {
  rows: ChampRow[];
  activeColumns: RowColumn[];
}) {
  return (
    <div className={styles.root}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Champion</th>
            {activeColumns.map((col) => (
              <th key={col}>{COLUMN_HEADERS[col]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td className={styles.portraitCell}>
                <img src={r.data.icon_url} alt={r.name} className={styles.portrait} loading="lazy" />
              </td>
              {activeColumns.map((col) => renderCell(r, col))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
