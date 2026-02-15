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

export async function getChampData(championName: string): Promise<ChampDataResponse> {
  const res = await fetch(
    `/api/familledle/champ_data/${encodeURIComponent(championName)}`,
    { headers: { Accept: "application/json" } }
  );

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`getChampData failed (${res.status}) ${text}`);
  }
  return (await res.json()) as ChampDataResponse;
}

/* -------------------- Attempt guess -------------------- */

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

export async function postAttemptGuess(
  championName: string
): Promise<PostAttemptGuessResponse> {
  const res = await fetch(`/api/familledle/attempts/guess`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ champion_name: championName }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`postAttemptGuess failed (${res.status}) ${text}`);
  }

  return (await res.json()) as PostAttemptGuessResponse;
}

export async function getChampOfTheDay(): Promise<ChampDataResponse> {
  const res = await fetch(
    `/api/familledle/champ_of_the_day`,
    { headers: { Accept: "application/json" } }
  );

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`getChampData failed (${res.status}) ${text}`);
  }
  return (await res.json()) as ChampDataResponse;
}



