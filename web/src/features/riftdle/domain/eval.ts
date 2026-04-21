import type { Bucket,Cell, Dir, Prox } from "../types";

// --------------------
// Hue circulaire
// --------------------

// delta signé minimal sur un cercle [0..360) : résultat dans [-180, +180]
export function circularHueDelta(valueHue: number, targetHue: number): number {
  const a = ((valueHue % 360) + 360) % 360;
  const b = ((targetHue % 360) + 360) % 360;
  const d = a - b;
  return ((d + 540) % 360) - 180;
}

export function evalHue(
  valueHue: number,
  targetHue: number,
  thresholds: { equalMax: number; closeMax: number }
): Cell {
  const delta = circularHueDelta(valueHue, targetHue);
  const abs = Math.abs(delta);

  const dir: Dir = abs === 0 ? "equal" : delta > 0 ? "higher" : "lower";
  const prox: Prox =
    abs <= thresholds.equalMax ? "equal" : abs <= thresholds.closeMax ? "close" : "far";

  return { dir, prox, delta };
}


export function evalByDeltaInt(value: number, target: number, closeDelta: number): Cell {
  const delta = value - target;
  const dir: Dir = delta === 0 ? "equal" : delta > 0 ? "higher" : "lower";
  const prox: Prox = delta === 0 ? "equal" : Math.abs(delta) <= closeDelta ? "close" : "far";
  return { dir, prox, delta };
}


function bucketIndex(value: number, buckets: Bucket[]): number {
  const i = buckets.findIndex((b) => value >= b.min && value <= b.max);
  return i === -1 ? buckets.length : i;
}

function bucketName(value: number, buckets: Bucket[]): string {
  const i = bucketIndex(value, buckets);
  return i >= 0 && i < buckets.length ? buckets[i]!.name : "Out";
}

export function evalByBucketAdjacent(value: number, target: number, buckets: Bucket[]): Cell {
  const delta = value - target;
  const dir: Dir = delta === 0 ? "equal" : delta > 0 ? "higher" : "lower";

  const iv = bucketIndex(value, buckets);
  const it = bucketIndex(target, buckets);

  const prox: Prox = iv === it ? "equal" : Math.abs(iv - it) === 1 ? "close" : "far";

  return { dir, prox, delta, bucketName: bucketName(value, buckets) };
}

// --------------------
// family_mastery
// --------------------

export function evalFamily(
  value: string[],
  target: string[]
): Cell {
  const v = new Set(value);
  const t = new Set(target);

  // exception: si champ du jour vide
  if (t.size === 0) {
    return { prox: v.size === 0 ? "equal" : "far" };
  }

  let inter = 0;
  for (const x of v) if (t.has(x)) inter++;

  const equal = v.size === t.size && inter === t.size;
  const prox: Prox = equal ? "equal" : inter > 0 ? "close" : "far";
  return { prox, delta: inter }; // delta = nb d'intersections (optionnel)
}
