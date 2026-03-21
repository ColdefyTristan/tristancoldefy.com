export type Dir = "higher" | "lower" | "equal";
export type Prox = "equal" | "close" | "far";

export type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string };

export type ClueType = "date" | "genre" | "espece" | "region" | "ressource" | "position";

export type RowColumn =
  | "skin_number"
  | "family_mastery"
  | "colorwheel"
  | "mobility"
  | "randomness"
  | "cc_quantity"
  | "intension"
  | "vote"
  | "regime"
  | "pilosite"
  | "genre"
  | "ressource"
  | "portee"
  | "annee_sortie"
  | "role"
  | "espece"
  | "region";

export type BuildRowRules = {
  skinCloseDelta: number;
  hue: { equalMax: number; closeMax: number };
  buckets: {
    mobility: Bucket[];
    randomness: Bucket[];
    cc_quantity: Bucket[];
    intension: Bucket[];
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
    intension: Cell;
    vote: Cell;
    regime: Cell;
    pilosite: Cell;
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
  intension: number;
  vote: string[];
  regime: string[];
  pilosite: string[];
  genre: string | null;
  ressource: string | null;
  portee: string | null;
  annee_sortie: string | null;
  role: string[];
  espece: string[];
  region: string[];
  icon_url: string;
  mean_hex: string;
  mean_hue: number;
  // Rangs parmi tous les champions (retournés uniquement par /champ_data)
  mobility_rank?: number;
  randomness_rank?: number;
  cc_quantity_rank?: number;
  intension_rank?: number;
  total_champions?: number;
};

export type ChampDataResponse = {
  name: string;
  data: ChampDataOut;
};

export type DailyGameResponse = {
  day: string; // "YYYY-MM-DD"
  champ_name: string;
  row_columns: RowColumn[];
  winner_count: number;
};

export type FamilledleAttemptDayOut = {
  day: string; // "YYYY-MM-DD"
  is_finished: boolean;
  champions: string[];
  clues: ClueType[];
  clue_points: number;
};

export type FamilledleAttemptTodayWrapperOut = {
  exists: boolean;
  attempt: FamilledleAttemptDayOut | null;
};

export type AttemptOut = {
  id: number;
  day: string;
  try_count: number;
  finished_at: string | null;
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
