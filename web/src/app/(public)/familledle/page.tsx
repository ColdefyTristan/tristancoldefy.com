"use client";

import { useEffect, useMemo, useState } from "react";
import SearchComboBox from "@/components/ui/SearchComboBox";
import RowTable from "@/components/layout/RowTable"; 
import champTerms from "@/data/champTerms.json";
import styles from "./page.module.css";

import { getChampData,postAttemptGuess, getChampOfTheDay,ChampDataResponse } from "@/lib/api/champData"; 
import { buildRow, type ChampRow, type BuildRowRules } from "@/lib/champData/buildRow";

// --- RULES au niveau module ---
const RULES: BuildRowRules = {
  skinCloseDelta: 2,
  hue: { equalMax: 10, closeMax: 40 },
  buckets: {
    mobility: [
      { name: "I am speed", min: 0, max: 11 },
      { name: "Vite vite", min: 12, max: 47 },
      { name: "ça se débrouille", min: 48, max: 108 },
      { name: "Pas ouf", min: 110, max: 149 },
      { name: "Tristement lent", min: 150, max: 999 },
    ],
    randomness: [
      { name: "Connu",           min: 135, max: 173 }, 
      { name: "C'est ok",        min: 38,  max: 134 }, 
      { name: "Vite fait random",min: 14,  max: 37  }, 
      { name: "Méga random",     min: 1,   max: 13  },
    ],
    cc_quantity: [
      { name: "Horreur", min: 0, max: 16 },
      { name: "Relou", min: 17, max: 43 },
      { name: "C'est ok", min: 44, max: 127 },
      { name: "Anedoctique", min: 128, max: 157 },
      { name: "Absence de CC", min: 158, max: 999 },
    ],
  },
};

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string };

export default function ChampionsPage() {
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [rows, setRows] = useState<ChampRow[]>([]);
  const [champOfTheDay, setChampOfTheDay] = useState<ChampDataResponse | null>(null);

  const champsIds = useMemo(() => champTerms.champions.map((c) => c.id), []);
  const allowed = useMemo(() => new Set(champsIds), [champsIds]);
  const ready = champOfTheDay !== null;
  const canSubmit = ready && allowed.has(input.trim().toLowerCase());
  
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
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    setStatus({ kind: "error", message: msg });
  }
}



  return (
    <div className={styles.root}>
      <RowTable rows={rows} />

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
