export type ConditionOut = {
  id: string;
  label: string;
  weight: number;
  total: number;
  known: number;
};

export type GroupOut = {
  conditions: ConditionOut[];
  total: number;
  known: number;
};

export type CellOut = {
  total: number;
  known: number;
};

export type GridOut = {
  id: number;
  difficulty: 'easy' | 'medium' | 'hard';
  score: number;
  difficulty_score: number;
  rows: GroupOut[];
  cols: GroupOut[];
  cells: CellOut[][];
};

export type DailyGameOut = {
  id: number;
  day: string;
  easy: GridOut | null;
  medium: GridOut | null;
  hard: GridOut | null;
};

export type CardEntry = {
  name: string;
  oracle_id: string;
  image_url_medium: string | null;
};

export type CardNamesOut = {
  lang: string;
  cards: CardEntry[];
};

export type GuessOut = {
  id: number;
  position: number;
  difficulty: string;
  cell_row: number;
  cell_col: number;
  oracle_id: string;
  card_name: string;
  is_valid: boolean;
};

export type AttemptOut = {
  id: number;          // -1 for anonymous (local only)
  day: string;
  won_easy: boolean;
  won_medium: boolean;
  won_hard: boolean;
  finished_at: string | null;
  guesses: GuessOut[];
};

export type GuessIn = {
  difficulty: string;
  cell_row: number;
  cell_col: number;
  oracle_id: string;
};

export type GuessResultOut = {
  is_valid: boolean;
  oracle_id: string;
  card_name: string | null;
  attempt: AttemptOut | null;  // null for anonymous
};
