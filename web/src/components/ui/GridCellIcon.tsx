type Props = {
  /** Selected row (0–2) */
  row: 0 | 1 | 2;
  /** Selected column (0–2) */
  col: 0 | 1 | 2;
  /** SVG size — any CSS length, defaults to "1em" */
  size?: number | string;
  /** Stroke + fill color, defaults to "currentColor" */
  color?: string;
  className?: string;
};

/**
 * Small 3×3 grid icon with a dot in the selected cell.
 * Renders at text size by default — use as an inline icon.
 *
 * Example:
 *   <GridCellIcon row={1} col={2} />
 *   <GridCellIcon row={0} col={0} size="1.4em" color="#8b5cf6" />
 */
export default function GridCellIcon({ row, col, size = '1em', color = 'currentColor', className }: Props) {
  // ViewBox is 18×18. Each cell is 6×6.
  // Grid lines at 6 and 12 on each axis.
  const cx = col * 6 + 3;
  const cy = row * 6 + 3;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 18 18"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}
    >
      {/* 2 vertical dividers */}
      <line x1="6"  y1="0" x2="6"  y2="18" stroke={color} strokeWidth="1" />
      <line x1="12" y1="0" x2="12" y2="18" stroke={color} strokeWidth="1" />

      {/* 2 horizontal dividers */}
      <line x1="0" y1="6"  x2="18" y2="6"  stroke={color} strokeWidth="1" />
      <line x1="0" y1="12" x2="18" y2="12" stroke={color} strokeWidth="1" />

      {/* Dot in selected cell */}
      <circle cx={cx} cy={cy} r="2" fill={color} />
    </svg>
  );
}
