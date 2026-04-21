import { api } from "@/lib/api/client";

import { ChampDataResponse, DailyGameResponse, PostAttemptGuessResponse } from "../types";

export async function getChampData(championName: string): Promise<ChampDataResponse> {
  return api.get<ChampDataResponse>(`/riftdle/champ_data/${encodeURIComponent(championName)}`);
}

export async function postAttemptGuess(championName: string): Promise<PostAttemptGuessResponse> {
  return api.post<PostAttemptGuessResponse>("/riftdle/attempts/guess", { champion_name: championName });
}

export async function getDailyGame(): Promise<DailyGameResponse> {
  return api.get<DailyGameResponse>("/riftdle/daily_game");
}
