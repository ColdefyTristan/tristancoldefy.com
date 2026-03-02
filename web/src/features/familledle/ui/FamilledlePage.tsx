"use client";

import { useEffect, useMemo, useState } from "react";
import SearchComboBox from "@/components/ui/SearchComboBox";
import RowTable from "@/components/layout/RowTable"; 
import champTerms from "../data/champTerms.json";
import styles from "./Familledle.module.css";

import { buildRow} from "../domain/buildRow";
import { type ChampRow, type ChampDataResponse, type Status  } from "../types";
import { getChampData,postAttemptGuess,getChampOfTheDay} from "../api/client";
import { getTodayAttempt } from "../api/attempst";
import { RULES } from "../domain/rules"; 

export default function FamilledlePage() {
  const normalize = (s: string) => s.trim().toLowerCase();

  const [input, setInput] = useState("");

  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [rows, setRows] = useState<ChampRow[]>([]);
  const [champOfTheDay, setChampOfTheDay] = useState<ChampDataResponse | null>(null);

  const [todayAttemptChampions, setTodayAttemptChampions] = useState<string[] | null>(null);
  const [todayAttemptFinished, setTodayAttemptFinished] = useState(false);


  
  const normalizedInput = normalize(input);


  const champsIds = useMemo(() => champTerms.champions.map((c) => c.id), []);
  const allowed = useMemo(() => new Set(champsIds), [champsIds]);
  const ready = champOfTheDay !== null;
  const canSubmit = ready && allowed.has(normalizedInput);
  
  // Charger le champ du jour une fois
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const day = await getChampOfTheDay(); // ChampDataResponse
        if (!cancelled) setChampOfTheDay(day);
      } catch (e) {
        if (!cancelled) setChampOfTheDay(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
  let cancelled = false;

  (async () => {
    try {
      const wrapper = await getTodayAttempt(); // { exists, attempt }
      if (cancelled) return;

      if (!wrapper.exists || !wrapper.attempt) {
        setTodayAttemptChampions(null);
        setTodayAttemptFinished(false);
        return;
      }

      setTodayAttemptChampions(wrapper.attempt.champions);
      setTodayAttemptFinished(wrapper.attempt.is_finished);
    } catch (e) {
      // not connected is ok
      return;
    }
  })();

  return () => {
    cancelled = true;
  };
}, []);

    useEffect(() => {
    if (!champOfTheDay) return;
    if (!todayAttemptChampions || todayAttemptChampions.length === 0) return;

    let cancelled = false;

    (async () => {
        try {
        // fetch champ data pour chaque guess (ordre conservé)
        const champs = await Promise.all(todayAttemptChampions.map((n) => getChampData(n)));
        if (cancelled) return;

        const built = champs.map((c) => buildRow(c, champOfTheDay, RULES));
        setRows(built);
        } catch {
        // si ça rate, on ne bloque pas la page
        }
    })();

    return () => {
        cancelled = true;
    };
    }, [champOfTheDay, todayAttemptChampions]);


  async function submitCurrent() {
    if (!canSubmit || !champOfTheDay) return;
    const name = input.trim();
    if (!name) return;

    setStatus({ kind: "loading" });
    try {
        const attemptRes = await postAttemptGuess(name);
        const champRes = await getChampData(name);
        setRows((prev) => [...prev, buildRow(champRes, champOfTheDay, RULES)]);
        setStatus({ kind: "idle" });
        setInput("");
        if (attemptRes.guess.is_correct) {
            setTodayAttemptFinished(true);
        }
    } catch (e) {
        const msg = e instanceof Error ? e.message : "Unknown error";
        setStatus({ kind: "error", message: msg });
    }
  }



  return (
    <div className={styles.root}>
      <RowTable rows={rows} />
      {todayAttemptFinished && (
        <div className={styles.centerResult}>
            <div className={styles.winAnnounce}>
                <h2>Bravo ! Vous avez gagné !</h2>
                <h3>Score : {todayAttemptChampions && todayAttemptChampions.length}</h3>
            </div>
        </div>
      )}

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          void submitCurrent();
        }}
      >
        <SearchComboBox
          terms={champsIds}
          value={input}
          onValueChange={setInput}
          placeholder={ready ? "Choisir un champion…" : "Chargement du champion du jour…"}
          maxSuggestions={8}
        />

        <button
          type="submit"
          className={styles.btn}
          disabled={!canSubmit || status.kind === "loading"}
        >
          {status.kind === "loading" ? "Chargement…" : "Selectionner champion"}
        </button>

        {!ready ? <div className={styles.hint}>Récupération du champion du jour…</div> : null}

        {ready && !allowed.has(input) && input.trim() ? (
          <div className={styles.hint}>Choisis un élément dans la liste.</div>
        ) : null}
      </form>

      

      {status.kind === "error" ? <div className={styles.error}>{status.message}</div> : null}
    </div>
  );
}
