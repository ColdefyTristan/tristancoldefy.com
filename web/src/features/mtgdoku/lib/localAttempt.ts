import { AttemptOut, GuessOut, GuessResultOut } from '../types';

const KEY_PREFIX = 'mtgdoku:attempt:';

function storageKey(day: string) {
  return `${KEY_PREFIX}${day}`;
}

export function loadLocalAttempt(day: string): AttemptOut | null {
  try {
    const raw = localStorage.getItem(storageKey(day));
    if (!raw) return null;
    return JSON.parse(raw) as AttemptOut;
  } catch {
    return null;
  }
}

export function saveLocalAttempt(attempt: AttemptOut): void {
  try {
    localStorage.setItem(storageKey(attempt.day), JSON.stringify(attempt));
  } catch {
    // localStorage peut être indisponible (mode privé strict, quota dépassé)
  }
}

/** Construit un attempt local vide pour un jour donné (utilisateur anonyme). */
export function createLocalAttempt(day: string): AttemptOut {
  return {
    id: -1,
    day,
    won_easy: false,
    won_medium: false,
    won_hard: false,
    finished_at: null,
    guesses: [],
  };
}

/**
 * Applique le résultat d'un guess à un attempt local et le persiste.
 * Retourne l'attempt mis à jour.
 */
export function applyGuessToLocalAttempt(
  attempt: AttemptOut,
  result: GuessResultOut,
  difficulty: string,
  cell_row: number,
  cell_col: number,
): AttemptOut {
  const newGuess: GuessOut = {
    id: -(attempt.guesses.length + 1),  // id fictif négatif
    position: attempt.guesses.length,
    difficulty,
    cell_row,
    cell_col,
    oracle_id: result.oracle_id,
    card_name: result.card_name ?? '',
    is_valid: result.is_valid,
  };

  const updated: AttemptOut = {
    ...attempt,
    guesses: [...attempt.guesses, newGuess],
    won_easy: attempt.won_easy || (result.is_valid && difficulty === 'easy'),
    won_medium: attempt.won_medium || (result.is_valid && difficulty === 'medium'),
    won_hard: attempt.won_hard || (result.is_valid && difficulty === 'hard'),
  };

  saveLocalAttempt(updated);
  return updated;
}
