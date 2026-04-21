"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import BlobBackground, { PRESET_EMBER } from "@/components/ui/BlobBackground";
import SearchComboBox from "@/components/ui/SearchComboBox";

import champTerms from "../data/champTerms.json";
import { useDailyGame } from "../hooks/useChampOfTheDay";
import { useRiftdleGame } from "../hooks/useRiftdleGame";
import type { ChampDataOut, ClueType } from "../types";
import GameBar from "./GameBar";
import styles from "./Riftdle.module.css";
import RowTable from "./RowTable";

const normalize = (s: string) => s.trim().toLowerCase();

const allChampNames = champTerms.champions.map((c) => c.name);
const nameToId = new Map(champTerms.champions.map((c) => [normalize(c.name), c.id]));

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

export default function RiftdlePage() {
  const [input, setInput] = useState("");
  const [selectedBarIndices, setSelectedBarIndices] = useState<number[]>([]);

  const { user } = useAuth();
  const { dailyGame, champOfTheDay, isLoading, error: champError } = useDailyGame();
  const { rows, isFinished, submitStatus, usedClues, cluePoints, revealClue, submit } = useRiftdleGame(champOfTheDay, dailyGame);

  const activeColumns = (dailyGame?.row_columns ?? []).filter(
    (col) => col !== "family_mastery" || (!!user && user.is_family),
  );

  useEffect(() => {
    if (usedClues.length === 0) return;
    setSelectedBarIndices(usedClues.map((c) => CLUE_TYPES.indexOf(c)).filter((i) => i !== -1));
  }, [usedClues]);

  const normalizedInput = normalize(input);
  const ready = champOfTheDay !== null;

  const availableNames = useMemo(() => {
    const usedNames = new Set(rows.map((r) => normalize(r.name)));
    return allChampNames.filter((name) => !usedNames.has(normalize(name)));
  }, [rows]);

  const availableNamesNormalized = useMemo(() => new Set(availableNames.map(normalize)), [availableNames]);
  const canSubmit = ready && availableNamesNormalized.has(normalizedInput);

  const guessCount = rows.length;

  async function submitChamp(name: string) {
    if (!ready) return;
    const id = nameToId.get(normalize(name));
    if (!id) return;
    await submit(id);
    setInput("");
  }

  async function handleSubmit() {
    if (!canSubmit) return;
    await submitChamp(input);
  }

  return (
    <div className={styles.root}>
      <BlobBackground blobs={PRESET_EMBER} />
      <header className={styles.header}>
        <h1 className={styles.title}>Riftdle</h1>
        <p className={styles.subtitle}>Trouvez le champion du jour avec les catégories disponibles</p>
        {dailyGame && (
          <p className={styles.day}>
            Champion du {new Date(dailyGame.day).toLocaleDateString('fr-FR', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        )}
      </header>
      <RowTable rows={rows} activeColumns={activeColumns} />

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
          terms={availableNames}
          value={input}
          onValueChange={setInput}
          onSelect={(name) => void submitChamp(name)}
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
        {ready && !availableNamesNormalized.has(normalizedInput) && input.trim() && (
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
