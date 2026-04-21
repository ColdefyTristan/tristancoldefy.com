'use client';

import Fuse from 'fuse.js';
import Link from 'next/link';
import React from 'react';
import { useEffect, useRef, useState } from 'react';

import { useAuth } from '@/components/auth/AuthProvider';
import BlobBackground, { PRESET_VIOLET } from '@/components/ui/BlobBackground';
import GridCellIcon from '@/components/ui/GridCellIcon';

import { getCardNames, getDailyGame, getTodayAttempt, postGuess } from '../api/client';
import { applyGuessToLocalAttempt, createLocalAttempt, loadLocalAttempt } from '../lib/localAttempt';
import { AttemptOut, CardEntry, DailyGameOut, GridOut, GuessOut } from '../types';
import ConditionPill from './ConditionPill';
import styles from './MtgDoku.module.css';

const MAX_SUGGESTIONS = 12;

export type Difficulty = 'easy' | 'medium' | 'hard';

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  easy: 'Facile',
  medium: 'Moyen',
  hard: 'Difficile',
};

type Props = { difficulty: Difficulty };

export default function MtgDokuPage({ difficulty }: Props) {
  const { status } = useAuth();
  const [game, setGame] = useState<DailyGameOut | null>(null);
  const [attempt, setAttempt] = useState<AttemptOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCell, setSelectedCell] = useState<{ r: number; c: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<CardEntry[]>([]);
  const [selectedCard, setSelectedCard] = useState<CardEntry | null>(null);
  const [wrongCard, setWrongCard] = useState<CardEntry | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cardsLoaded, setCardsLoaded] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const fuseRef = useRef<Fuse<CardEntry> | null>(null);
  const cardsMapRef = useRef<Map<string, CardEntry>>(new Map());

  // Charge la partie du jour + les noms de cartes au montage
  useEffect(() => {
    getDailyGame()
      .then(setGame)
      .catch((e) => setError(e.message ?? 'Erreur inconnue'));

    getCardNames().then(({ cards }) => {
      if (!Array.isArray(cards) || cards.length === 0) return;
      const map = new Map<string, CardEntry>();
      cards.forEach((c) => map.set(c.oracle_id, c));
      cardsMapRef.current = map;
      setCardsLoaded(true);
      fuseRef.current = new Fuse(cards, {
        keys: ['name'],
        threshold: 0.35,
        distance: 200,
        minMatchCharLength: 2,
      });
    }).catch(() => {});
  }, []);

  // Charge l'attempt une fois que la partie et le statut d'auth sont connus
  useEffect(() => {
    if (!game) return;
    if (status === 'authenticated') {
      getTodayAttempt().then(setAttempt);
    } else {
      setAttempt(loadLocalAttempt(game.day));
    }
  }, [game, status]);

  useEffect(() => {
    if (selectedCell) {
      setSearchQuery('');
      setSuggestions([]);
      setSelectedCard(null);
      setWrongCard(null);
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [selectedCell]);

  function handleSearchChange(value: string) {
    setSearchQuery(value);
    setSelectedCard(null);
    if (!value.trim() || !fuseRef.current) {
      setSuggestions([]);
      return;
    }
    const results = fuseRef.current.search(value, { limit: MAX_SUGGESTIONS });
    setSuggestions(results.map((r) => r.item));
  }

  function selectSuggestion(card: CardEntry) {
    setSearchQuery(card.name);
    setSelectedCard(card);
    setSuggestions([]);
  }

  async function submitGuess(oracleId: string) {
    if (!selectedCell || !game) return;
    const { r: cell_row, c: cell_col } = selectedCell;

    setIsSubmitting(true);
    try {
      const result = await postGuess({ difficulty, cell_row, cell_col, oracle_id: oracleId });

      if (status === 'authenticated' && result.attempt) {
        setAttempt(result.attempt);
      } else {
        const base = attempt ?? createLocalAttempt(game.day);
        setAttempt(applyGuessToLocalAttempt(base, result, difficulty, cell_row, cell_col));
      }

      if (result.is_valid) {
        closeModal();
      } else {
        setWrongCard(selectedCard);
        setSelectedCard(null);
        setSearchQuery('');
      }
    } catch (e: any) {
      // CARD_ALREADY_TRIED / CELL_ALREADY_WON → silencieux
      if (e?.status === 409) return;
      setError(e.message ?? 'Erreur lors de l\'envoi');
    } finally {
      setIsSubmitting(false);
    }
  }

  const grid: GridOut | null = game?.[difficulty] ?? null;

  function getValidGuess(r: number, c: number): GuessOut | null {
    return attempt?.guesses.find(
      (g) => g.is_valid && g.difficulty === difficulty && g.cell_row === r && g.cell_col === c
    ) ?? null;
  }

  function cornerClass(r: number, c: number): string {
    if (r === 0 && c === 0) return styles.gameCellTopLeft;
    if (r === 0 && c === 2) return styles.gameCellTopRight;
    if (r === 2 && c === 0) return styles.gameCellBottomLeft;
    if (r === 2 && c === 2) return styles.gameCellBottomRight;
    return '';
  }

  function closeModal() {
    setSelectedCell(null);
    setSearchQuery('');
    setSuggestions([]);
  }

  const rowConds = selectedCell ? (grid?.rows[selectedCell.r]?.conditions ?? []) : [];
  const colConds = selectedCell ? (grid?.cols[selectedCell.c]?.conditions ?? []) : [];

  return (
    <div className={styles.page}>
      <BlobBackground blobs={PRESET_VIOLET} />
      <div className={styles.titleRow}>
        <Link href="/mtgdoku" className={styles.backLink}>← MtgDoku</Link>
        <h1 className={styles.title}>{DIFFICULTY_LABEL[difficulty]}</h1>
      </div>

      {error && <p className={styles.errorMsg}>Erreur : {error}</p>}

      <div className={styles.layout}>
        <div className={styles.gridWrapper}>
          <div className={styles.grid}>
            {/* Row 0, Col 0 — corner */}
            <div className={styles.cornerCell} />

            {/* Row 0, Cols 1-3 — column headers */}
            {[0, 1, 2].map((c) => (
              <div key={`col-header-${c}`} className={styles.headerCell}>
                {grid?.cols[c]?.conditions.map((cond) => (
                  <ConditionPill key={cond.id} condition={cond} />
                ))}
              </div>
            ))}

            {/* Rows 1-3 */}
            {[0, 1, 2].map((r) => (
              <React.Fragment key={r}>
                {/* Col 0 — row header */}
                <div key={`row-header-${r}`} className={styles.headerCell}>
                  {grid?.rows[r]?.conditions.map((cond) => (
                    <ConditionPill key={cond.id} condition={cond} />
                  ))}
                </div>

                {/* Cols 1-3 — game cells */}
                {[0, 1, 2].map((c) => {
                  const validGuess = getValidGuess(r, c);
                  const solvedCard = validGuess ? cardsMapRef.current.get(validGuess.oracle_id) : null;
                  return (
                    <div
                      key={`cell-${r}-${c}`}
                      className={`${styles.gameCell} ${cornerClass(r, c)} ${solvedCard ? styles.gameCellSolved : ''}`}
                      onClick={solvedCard ? undefined : () => setSelectedCell({ r, c })}
                    >
                      {solvedCard?.image_url_medium ? (
                        <img
                          src={solvedCard.image_url_medium}
                          alt={solvedCard.name}
                          className={styles.cellCardImage}
                        />
                      ) : (
                        <>
                          <div className={styles.gameCellInner}>✦</div>
                          {grid?.cells[r][c] != null && (
                            <div className={styles.cellHint}>
                              {grid.cells[r][c].total} cartes possibles
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
              </React.Fragment>
            ))}
          </div>
        </div>

        <aside className={styles.sidebar}>
          <p className={styles.sidebarTitle}>Cartes essayées</p>
          {(() => {
            const tried = attempt?.guesses.filter((g) => g.difficulty === difficulty) ?? [];
            return tried.length === 0 ? (
              <p className={styles.sidebarEmpty}>Aucune carte essayée pour l&apos;instant.</p>
            ) : (
              <ul className={styles.triedList}>
                {tried.map((g) => (
                  <li key={g.id} className={`${styles.triedItem} ${g.is_valid ? styles.triedValid : styles.triedInvalid}`}>
                    <GridCellIcon row={g.cell_row as 0|1|2} col={g.cell_col as 0|1|2} size="1em" />
                    {g.card_name}
                  </li>
                ))}
              </ul>
            );
          })()}
        </aside>
      </div>

      {!game && !error && <p className={styles.statusMsg}>Chargement de la partie du jour…</p>}

      {/* Cell modal */}
      {selectedCell && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            {/* Conditions header + close button */}
            
            <div className={styles.modalHeader}>
              <GridCellIcon
                row={selectedCell.r as 0 | 1 | 2}
                col={selectedCell.c as 0 | 1 | 2}
                size="1.5em"
              />

              <div className={styles.modalCondGroup}>
                {rowConds.map((cond) => (
                  <ConditionPill key={cond.id} condition={cond} />
                ))}
              </div>
              <span className={styles.modalSep}>×</span>
              <div className={styles.modalCondGroup}>
                {colConds.map((cond) => (
                  <ConditionPill key={cond.id} condition={cond} />
                ))}
              </div>
              <button className={styles.modalCloseBtn} onClick={closeModal} aria-label="Fermer">
                ✕
              </button>
            </div>

            {/* Body: search group, validate, [wrong card image] */}
            <div className={styles.modalBody}>
              <div className={styles.modalSearchGroup}>
                <input
                  ref={searchInputRef}
                  className={styles.modalSearchInput}
                  type="text"
                  placeholder="Rechercher une carte…"
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                />
                {suggestions.length > 0 && (
                  <div className={styles.modalSuggestions}>
                    {suggestions.map((card) => (
                      <button
                        key={card.oracle_id}
                        className={styles.suggestionItem}
                        onClick={() => selectSuggestion(card)}
                      >
                        {card.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                className={styles.modalValidateBtn}
                disabled={!selectedCard || isSubmitting}
                onClick={() => selectedCard && submitGuess(selectedCard.oracle_id)}
              >
                {isSubmitting ? '…' : 'Valider'}
              </button>

              {wrongCard?.image_url_medium && (
                <div className={styles.wrongCardWrapper}>
                  <img
                    src={wrongCard.image_url_medium}
                    alt={wrongCard.name}
                    className={styles.wrongCardImage}
                  />
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
