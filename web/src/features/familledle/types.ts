type Dir = "higher" | "lower" | "equal";
type Prox = "equal" | "close" | "far";

export type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string };

export type BuildRowRules = {
  skinCloseDelta: number; // distance int
  hue: { equalMax: number; closeMax: number }; // degrés
  buckets: {
    mobility: Bucket[];
    randomness: Bucket[];
    cc_quantity: Bucket[];
  };
};

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

export type ChampDataOut = {
  skin_number: number;
  family_mastery: string[];
  mobility: number;
  randomness: number;
  cc_quantity: number;
  icon_url: string;
  mean_hex: string;
  mean_hue: number;
  is_champ_of_the_day?: boolean;
};

export type ChampDataResponse = {
  name: string;
  data: ChampDataOut;
};

export type FamilledleAttemptDayOut = {
  day: string; // "YYYY-MM-DD"
  is_finished: boolean;
  champions: string[];
};

export type FamilledleAttemptTodayWrapperOut = {
  exists: boolean;
  attempt: FamilledleAttemptDayOut | null;
};

export type AttemptOut = {
  id: number;
  day: string; // ISO date: "2026-02-15"
  try_count: number;
  finished_at: string | null; // ISO datetime or null
};

export type AttemptGuessOut = {
  position: number;
  champion_name: string;
  is_correct: boolean;
};

export type PostAttemptGuessResponse = {
  attempt: AttemptOut;
  guess: AttemptGuessOut;
};