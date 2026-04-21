import { api } from '@/lib/api/client';
import { ApiError } from '@/lib/api/errors';

import { AttemptOut, CardNamesOut, DailyGameOut, GuessIn, GuessResultOut } from '../types';

export async function getDailyGame(): Promise<DailyGameOut> {
  return api.get<DailyGameOut>('/mtgdoku/daily');
}

export async function getCardNames(): Promise<CardNamesOut> {
  return api.get<CardNamesOut>('/mtgdoku/cards/names');
}

/** Retourne l'attempt du jour pour l'utilisateur connecté, ou null s'il n'en a pas encore. */
export async function getTodayAttempt(): Promise<AttemptOut | null> {
  try {
    return await api.get<AttemptOut>('/mtgdoku/daily/attempt');
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export async function postGuess(body: GuessIn): Promise<GuessResultOut> {
  return api.post<GuessResultOut>('/mtgdoku/daily/guess', body);
}
