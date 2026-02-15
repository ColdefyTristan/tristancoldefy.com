"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./SearchComboBox.module.css";

type Props = {
  terms: string[];
  placeholder?: string;
  maxSuggestions?: number;
  onSelect?: (value: string) => void;

  // NEW (optional): controlled mode
  value?: string;
  onValueChange?: (value: string) => void;
};

export default function SearchComboBox({
  terms,
  placeholder = "Rechercher…",
  maxSuggestions = 8,
  onSelect,
  value,
  onValueChange,
}: Props) {
  const [internal, setInternal] = useState("");
  const query = value ?? internal;

  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const rootRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const listId = "search-combobox-list";
  const activeId = activeIndex >= 0 ? `search-option-${activeIndex}` : undefined;

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const scored = terms
      .map((t) => {
        const tl = t.toLowerCase();
        const idx = tl.indexOf(q);
        if (idx === -1) return null;
        const score = idx === 0 ? 0 : 1;
        return { t, score };
      })
      .filter(Boolean) as { t: string; score: number }[];

    scored.sort((a, b) => a.score - b.score || a.t.localeCompare(b.t));
    return scored.slice(0, maxSuggestions).map((x) => x.t);
  }, [terms, query, maxSuggestions]);

  useEffect(() => {
    setActiveIndex(-1);
  }, [query]);

  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, []);

  function setQuery(next: string) {
    if (onValueChange) onValueChange(next);
    else setInternal(next);
  }

  function commit(next: string) {
    setQuery(next);
    setOpen(false);
    setActiveIndex(-1);
    onSelect?.(next);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      setOpen(true);
      return;
    }
    if (e.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
      return;
    }
    if (!suggestions.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      if (open && activeIndex >= 0) {
        e.preventDefault();
        commit(suggestions[activeIndex]);
      }
    }
  }

  const hasSuggestions = suggestions.length > 0;

  return (
    <div ref={rootRef} className={styles.root}>
      <div className={styles.inputWrap}>
        <input
          ref={inputRef}
          className={styles.input}
          value={query}
          placeholder={placeholder}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open && hasSuggestions}
          aria-controls={listId}
          aria-activedescendant={activeId}
        />

        {query ? (
          <button
            type="button"
            className={styles.clear}
            aria-label="Effacer"
            onClick={() => {
              setQuery("");
              setOpen(false);
              inputRef.current?.focus();
            }}
          >
            ×
          </button>
        ) : null}
      </div>

      {open && hasSuggestions ? (
        <ul id={listId} className={styles.list} role="listbox">
          {suggestions.map((s, i) => (
            <li
              key={`${s}-${i}`}
              id={`search-option-${i}`}
              role="option"
              aria-selected={i === activeIndex}
              className={`${styles.item} ${i === activeIndex ? styles.itemActive : ""}`}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => commit(s)}
            >
              {s}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
