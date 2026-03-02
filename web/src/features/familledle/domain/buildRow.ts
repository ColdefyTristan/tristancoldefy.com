import type { ChampDataOut,ChampDataResponse,BuildRowRules,ChampRow } from "../types"; 
import {evalByDeltaInt,evalFamily,evalByBucketAdjacent,evalHue} from "./eval"


function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}




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
