"use client";

import { useEffect, useMemo, useState } from "react";
import SearchComboBox from "@/components/ui/SearchComboBox";
import champTerms from "../data/champTerms.json";
import styles from "./Familledle.module.css";

import GameBar from "./GameBar";
import RowTable from "./RowTable";
import { useDailyGame } from "../hooks/useChampOfTheDay";
import { useFamilledleGame } from "../hooks/useFamilledleGame";
import type { ChampDataOut, ClueType } from "../types";

const normalize = (s: string) => s.trim().toLowerCase();

const champsIds = champTerms.champions.map((c) => c.id);
const allowed = new Set(champsIds);

// L'ordre doit rester aligné avec CLUE_TYPES ci-dessous
const CLUE_TYPES: ClueType[] = ["date", "genre", "espece", "region", "ressource", "position"];

function buildClues(data: ChampDataOut): { label: string; value: string }[] {
  return [
    { label: "Année", value: data.annee_sortie ?? "?" },
    { label: "Genre", value: data.genre ?? "?" },
    { label: "Espèce", value: data.espece.join(", ") || "?" },
    { label: "Région", value: data.region.join(", ") || "?" },
    { label: "Ressource", value: data.ressource ?? "?" },
    { label: "Position", value: data.role.join(", ") || "?" },
  ];
}

export default function FamilledlePage() {
  const [input, setInput] = useState("");
  const [selectedBarIndices, setSelectedBarIndices] = useState<number[]>([]);

  const { dailyGame, champOfTheDay, isLoading, error: champError } = useDailyGame();
  const { rows, isFinished, submitStatus, usedClues, cluePoints, revealClue, submit } = useFamilledleGame(champOfTheDay);

  useEffect(() => {
    if (usedClues.length === 0) return;
    setSelectedBarIndices(usedClues.map((c) => CLUE_TYPES.indexOf(c)).filter((i) => i !== -1));
  }, [usedClues]);

  const normalizedInput = normalize(input);
  const ready = champOfTheDay !== null;
  const canSubmit = ready && allowed.has(normalizedInput);

  const guessCount = useMemo(() => rows.length, [rows]);

  async function handleSubmit() {
    if (!canSubmit) return;
    await submit(input.trim());
    setInput("");
  }

  return (
    <div className={styles.root}>
      <RowTable rows={rows} activeColumns={dailyGame?.row_columns ?? []} />

      {isFinished && (
        <div className={styles.centerResult}>
          <div className={styles.winAnnounce}>
            <h2>Bravo ! Vous avez gagné !</h2>
            <h3>Score : {guessCount}</h3>
          </div>
        </div>
      )}

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
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
          disabled={!canSubmit || submitStatus.kind === "loading"}
        >
          {submitStatus.kind === "loading" ? "Chargement…" : "Selectionner champion"}
        </button>

        {isLoading && <div className={styles.hint}>Récupération du champion du jour…</div>}
        {!!champError && (
          <div className={styles.error}>
            Impossible de charger le champion du jour. Réessayez plus tard.
          </div>
        )}
        {ready && !allowed.has(normalizedInput) && input.trim() && (
          <div className={styles.hint}>Choisis un élément dans la liste.</div>
        )}
      </form>

      {submitStatus.kind === "error" && (
        <div className={styles.error}>{submitStatus.message}</div>
      )}

      <GameBar
        clues={champOfTheDay ? buildClues(champOfTheDay.data) : []}
        selectedIndices={selectedBarIndices}
        cluePoints={cluePoints}
        isFinished={isFinished}
        onSelect={(i) => {
          setSelectedBarIndices((prev) => [...prev, i]);
          void revealClue(CLUE_TYPES[i]);
        }}
      />
    </div>
  );
}
