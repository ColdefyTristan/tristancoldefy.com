import type { BrowserAnim } from "../timeline/types";

export function BrowserPicto({ anim }: { anim: BrowserAnim }) {
  // viewBox 120x90
  const cursorX = anim.cursorX;
  const cursorY = anim.cursorY;

  // Card rect: x=18 y=36 w=52 h=22, origin left-center = (18, 47)
  const ox = 18;
  const oy = 47;
  const sx = anim.cardOpen;
  const sy = 0.25 + 0.75 * anim.cardOpen; // évite un "pop" trop sec

  const cardTransform = `translate(${ox} ${oy}) scale(${sx} ${sy}) translate(${-ox} ${-oy})`;

  return (
    <svg viewBox="0 0 120 90" aria-hidden="true" focusable="false">
      <rect
        x="6"
        y="6"
        width="108"
        height="78"
        rx="12"
        fill="rgba(255,255,255,0.03)"
        stroke="rgba(255,255,255,0.16)"
        strokeWidth="1.5"
      />

      <rect
        x="35"
        y="14"
        width="50"
        height="8"
        rx="4"
        fill="rgba(255,255,255,0.03)"
        stroke="rgba(255,255,255,0.16)"
        strokeWidth="1.5"
      />

      {/* dot */}
      <circle
        cx="22"
        cy="44"
        r="3"
        fill="rgba(255,255,255,0.30)"
        opacity={anim.dotAlpha}
      />

      {/* card */}
      <rect
        x="18"
        y="36"
        width="52"
        height="22"
        rx="7"
        fill="rgba(255,255,255,0.04)"
        stroke="rgba(255,255,255,0.16)"
        strokeWidth="1.5"
        opacity={anim.cardOpen > 0.001 ? 1 : 0}
        transform={cardTransform}
      />

      {/* cursor */}
      <g transform={`translate(${cursorX} ${cursorY})`}>
        <path
          d="M0 0 L0 20 L6 15 L10 24 L14 22 L10 13 L18 13 Z"
          fill="rgba(255,255,255,0.22)"
          stroke="rgba(255,255,255,0.18)"
          strokeWidth="1.2"
        />
      </g>
    </svg>
  );
}