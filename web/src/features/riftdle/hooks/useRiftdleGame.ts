import { useEffect, useState } from "react";

import { getTodayAttempt, postClue } from "../api/attempts";
import { getChampData, postAttemptGuess } from "../api/client";
import { buildRow } from "../domain/buildRow";
import { RULES } from "../domain/rules";
import type { ChampDataResponse, ChampRow, ClueType, DailyGameResponse, Status } from "../types";

const LOCAL_KEY = "riftdle_session";

type LocalSession = {
  day: string;
  champions: string[];
  clues: ClueType[];
  clue_points: number;
  is_finished: boolean;
};

function loadLocal(day: string): LocalSession | null {
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LocalSession;
    return parsed.day === day ? parsed : null;
  } catch {
    return null;
  }
}

function saveLocal(session: LocalSession) {
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(session));
  } catch {}
}

export type UseRiftdleGameResult = {
  rows: ChampRow[];
  isFinished: boolean;
  submitStatus: Status;
  usedClues: ClueType[];
  cluePoints: number;
  revealClue: (clue: ClueType) => Promise<void>;
  submit: (name: string) => Promise<void>;
};

export function useRiftdleGame(
  champOfTheDay: ChampDataResponse | null,
  dailyGame: DailyGameResponse | null,
): UseRiftdleGameResult {
  const [rows, setRows] = useState<ChampRow[]>([]);
  const [champions, setChampions] = useState<string[]>([]);
  const [isFinished, setIsFinished] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<Status>({ kind: "idle" });
  const [usedClues, setUsedClues] = useState<ClueType[]>([]);
  const [cluePoints, setCluePoints] = useState(0);

  // Charger l'historique du jour et reconstruire les rows une fois que champOfTheDay est prêt
  useEffect(() => {
    if (!champOfTheDay || !dailyGame) return;
    let cancelled = false;

    (async () => {
      try {
        const wrapper = await getTodayAttempt();
        if (cancelled) return;

        // Données serveur disponibles (utilisateur connecté avec un essai existant)
        if (wrapper.exists && wrapper.attempt) {
          setIsFinished(wrapper.attempt.is_finished);
          setUsedClues(wrapper.attempt.clues);
          setCluePoints(wrapper.attempt.clue_points);
          setChampions(wrapper.attempt.champions);

          if (wrapper.attempt.champions.length > 0) {
            const champs = await Promise.all(
              wrapper.attempt.champions.map((n) => getChampData(n))
            );
            if (cancelled) return;
            setRows(champs.map((c) => buildRow(c, champOfTheDay, RULES)));
          }
          return;
        }

        // Pas de données serveur : charger depuis localStorage (non connecté ou pas encore joué)
        const local = loadLocal(dailyGame.day);
        if (!local || local.champions.length === 0) return;

        setIsFinished(local.is_finished);
        setUsedClues(local.clues);
        setCluePoints(local.clue_points);
        setChampions(local.champions);

        const champs = await Promise.all(local.champions.map((n) => getChampData(n)));
        if (cancelled) return;
        setRows(champs.map((c) => buildRow(c, champOfTheDay, RULES)));
      } catch {
        // non connecté ou erreur réseau : on ne bloque pas le jeu
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [champOfTheDay, dailyGame]);

  async function submit(name: string): Promise<void> {
    if (!champOfTheDay || !dailyGame) return;
    setSubmitStatus({ kind: "loading" });
    try {
      const [attemptRes, champRes] = await Promise.all([
        postAttemptGuess(name),
        getChampData(name),
      ]);
      const newRow = buildRow(champRes, champOfTheDay, RULES);
      const isCorrect = attemptRes.guess.is_correct;
      const newChampions = [...champions, name];
      const newCluePoints = attemptRes.attempt
        ? (attemptRes.attempt.clue_points ?? Math.min(cluePoints + 1, 3))
        : Math.min(cluePoints + 1, 3);

      setRows((prev) => [...prev, newRow]);
      setChampions(newChampions);
      setCluePoints(newCluePoints);
      setSubmitStatus({ kind: "idle" });
      if (isCorrect) setIsFinished(true);

      saveLocal({
        day: dailyGame.day,
        champions: newChampions,
        clues: usedClues,
        clue_points: newCluePoints,
        is_finished: isCorrect,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setSubmitStatus({ kind: "error", message: msg });
    }
  }

  async function revealClue(clue: ClueType): Promise<void> {
    await postClue(clue); // ignore 401 silencieusement (non connecté)
    const newCluePoints = Math.max(cluePoints - 3, 0);
    const newClues = usedClues.includes(clue) ? usedClues : [...usedClues, clue];
    setCluePoints(newCluePoints);
    setUsedClues(newClues);

    if (dailyGame) {
      saveLocal({
        day: dailyGame.day,
        champions,
        clues: newClues,
        clue_points: newCluePoints,
        is_finished: isFinished,
      });
    }
  }

  return { rows, isFinished, submitStatus, usedClues, cluePoints, revealClue, submit };
}
