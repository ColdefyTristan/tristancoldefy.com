import { ChampDataResponse,PostAttemptGuessResponse } from "../types";
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



