import { useEffect, useState } from "react";
import { getTodayAttempt, postClue } from "../api/attempts";
import { getChampData, postAttemptGuess } from "../api/client";
import { buildRow } from "../domain/buildRow";
import { RULES } from "../domain/rules";
import type { ChampDataResponse, ChampRow, ClueType, Status } from "../types";

export type UseFamilledleGameResult = {
  rows: ChampRow[];
  isFinished: boolean;
  submitStatus: Status;
  usedClues: ClueType[];
  cluePoints: number;
  revealClue: (clue: ClueType) => Promise<void>;
  submit: (name: string) => Promise<void>;
};

export function useFamilledleGame(
  champOfTheDay: ChampDataResponse | null
): UseFamilledleGameResult {
  const [rows, setRows] = useState<ChampRow[]>([]);
  const [isFinished, setIsFinished] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<Status>({ kind: "idle" });
  const [usedClues, setUsedClues] = useState<ClueType[]>([]);
  const [cluePoints, setCluePoints] = useState(0);

  // Charger l'historique du jour et reconstruire les rows une fois que champOfTheDay est prêt
  useEffect(() => {
    if (!champOfTheDay) return;
    let cancelled = false;

    (async () => {
      try {
        const wrapper = await getTodayAttempt();
        if (cancelled) return;
        if (!wrapper.exists || !wrapper.attempt) return;

        setIsFinished(wrapper.attempt.is_finished);
        setUsedClues(wrapper.attempt.clues);
        setCluePoints(wrapper.attempt.clue_points);

        if (wrapper.attempt.champions.length > 0) {
          const champs = await Promise.all(
            wrapper.attempt.champions.map((n) => getChampData(n))
          );
          if (cancelled) return;
          setRows(champs.map((c) => buildRow(c, champOfTheDay, RULES)));
        }
      } catch {
        // non connecté ou erreur réseau : on ne bloque pas le jeu
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [champOfTheDay]);

  async function submit(name: string): Promise<void> {
    if (!champOfTheDay) return;
    setSubmitStatus({ kind: "loading" });
    try {
      const [attemptRes, champRes] = await Promise.all([
        postAttemptGuess(name),
        getChampData(name),
      ]);
      setRows((prev) => [...prev, buildRow(champRes, champOfTheDay, RULES)]);
      setSubmitStatus({ kind: "idle" });
      if (attemptRes.attempt) setCluePoints(attemptRes.attempt.clue_points ?? Math.min(cluePoints + 1, 3));
      else setCluePoints((p) => Math.min(p + 1, 3)); // non connecté
      if (attemptRes.guess.is_correct) setIsFinished(true);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setSubmitStatus({ kind: "error", message: msg });
    }
  }

  async function revealClue(clue: ClueType): Promise<void> {
    await postClue(clue); // ignore 401 silencieusement (non connecté)
    setCluePoints((p) => Math.max(p - 3, 0));
  }

  return { rows, isFinished, submitStatus, usedClues, cluePoints, revealClue, submit };
}
