import type { ChampDataOut,ChampDataResponse } from "@/lib/api/champData"; // adapte si besoin
import {evalByDeltaInt,evalFamily,evalByBucketAdjacent,evalHue} from "./eval"
type Dir = "higher" | "lower" | "equal";
type Prox = "equal" | "close" | "far";

export type Cell = { dir?: Dir; prox: Prox; delta?: number; bucketName?: string };


export type Bucket = { name: string; min: number; max: number };

export type ChampRow = {
  id: string;
  name: string;
  data: ChampDataOut;
  cells: {
    skin_number: Cell;
    family_mastery: Cell;
    mobility: Cell;
    randomness: Cell;
    cc_quantity: Cell;
    mean_hue: Cell;
    champOfTheDay: { value: boolean };
  };
};

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}


export type BuildRowRules = {
  skinCloseDelta: number; // distance int
  hue: { equalMax: number; closeMax: number }; // degrés
  buckets: {
    mobility: Bucket[];
    randomness: Bucket[];
    cc_quantity: Bucket[];
  };
};

export function buildRow(
  res: ChampDataResponse,
  champOfTheDay: ChampDataResponse,
  rules: BuildRowRules
): ChampRow {
  return {
    id: uid(),
    name: res.name,
    data: res.data,
    cells: {
      skin_number: evalByDeltaInt(res.data.skin_number, champOfTheDay.data.skin_number, rules.skinCloseDelta),
      family_mastery: evalFamily(res.data.family_mastery, champOfTheDay.data.family_mastery),
      mobility: evalByBucketAdjacent(res.data.mobility, champOfTheDay.data.mobility, rules.buckets.mobility),
      randomness: evalByBucketAdjacent(res.data.randomness, champOfTheDay.data.randomness, rules.buckets.randomness),
      cc_quantity: evalByBucketAdjacent(res.data.cc_quantity, champOfTheDay.data.cc_quantity, rules.buckets.cc_quantity),
      mean_hue: evalHue(res.data.mean_hue, champOfTheDay.data.mean_hue, rules.hue),
      champOfTheDay: { value: res.name === champOfTheDay.name },
    },
  };
}
