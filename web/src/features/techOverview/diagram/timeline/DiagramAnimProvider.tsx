"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { BROWSER_STEPS } from "./steps";
import type { BrowserAnim, DiagramAnimState } from "./types";

type Ctx = {
  state: DiagramAnimState;
  startOnce: () => void;
};

const DiagramAnimContext = createContext<Ctx | null>(null);

function easeInOutCubic(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function mixBrowser(from: BrowserAnim, to: BrowserAnim, t: number): BrowserAnim {
  return {
    cursorX: lerp(from.cursorX, to.cursorX, t),
    cursorY: lerp(from.cursorY, to.cursorY, t),
    cardOpen: lerp(from.cardOpen, to.cardOpen, t),
    dotAlpha: lerp(from.dotAlpha, to.dotAlpha, t),
  };
}

function getReducedMotion() {
  if (typeof window === "undefined") return false;
  return window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
}

const INITIAL_BROWSER: BrowserAnim = { cursorX: 60, cursorY: 52, cardOpen: 0, dotAlpha: 1 };

export function DiagramAnimProvider({
  children,
  observeRef,
}: {
  children: ReactNode;
  observeRef: React.RefObject<HTMLElement | null>;
}) {
  const [state, setState] = useState<DiagramAnimState>(() => ({
    browser: INITIAL_BROWSER,
    played: false,
    reduceMotion: false,
  }));

  const startedRef = useRef(false);
  const animationFrameIdRef = useRef<number | null>(null); //user for cancelAnimationFrame

  const startOnce = useCallback(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const reduce = getReducedMotion();
    if (reduce) {
      setState((s) => ({ ...s, reduceMotion: true, played: true, browser: INITIAL_BROWSER }));
      return;
    }

    let stepIndex = 0;
    let stepStart = performance.now();

    const tick = (now: number) => {
      const step = BROWSER_STEPS[stepIndex];
      const dt = now - stepStart;
      const rawT = Math.min(1, dt / step.durationMs);
      const stepProgressEased = easeInOutCubic(rawT);

      setState((s) => ({
        ...s,
        browser: mixBrowser(step.from, step.to, stepProgressEased),
      }));

      if (rawT >= 1) {
        stepIndex += 1;
        stepStart = now;

        if (stepIndex >= BROWSER_STEPS.length) {
          setState((s) => ({
            ...s,
            browser: INITIAL_BROWSER,
            played: true,
          }));
          animationFrameIdRef.current = null;
          return;
        }
      }

      animationFrameIdRef.current = requestAnimationFrame(tick);
    };

    animationFrameIdRef.current = requestAnimationFrame(tick);
  }, []);

  // Trigger 1: enter viewport (une fois)
  useEffect(() => {
    const observedElement = observeRef.current;
    if (!observedElement) return;

    const viewportObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) startOnce();
      },
      { threshold: 0.35 }
    );

    viewportObserver.observe(observedElement);
    return () => viewportObserver.disconnect();
  }, [observeRef, startOnce]);

  // Trigger 2/3: première interaction (hover/focus) si jamais l’IO ne déclenche pas
  useEffect(() => {
    const observedElement = observeRef.current;
    if (!observedElement) return;

    const onEnter = () => startOnce();
    const onFocusIn = () => startOnce();

    observedElement.addEventListener("pointerenter", onEnter, { once: true });
    observedElement.addEventListener("focusin", onFocusIn, { once: true });

    return () => {
      observedElement.removeEventListener("pointerenter", onEnter);
      observedElement.removeEventListener("focusin", onFocusIn);
    };
  }, [observeRef, startOnce]);

  useEffect(() => {
    return () => {
      if (animationFrameIdRef.current) cancelAnimationFrame(animationFrameIdRef.current);
    };
  }, []);

  const value = useMemo<Ctx>(() => ({ state, startOnce }), [state, startOnce]);

  return <DiagramAnimContext.Provider value={value}>{children}</DiagramAnimContext.Provider>;
}

export function useDiagramAnim() {
  const ctx = useContext(DiagramAnimContext);
  if (!ctx) throw new Error("useDiagramAnim must be used within DiagramAnimProvider");
  return ctx;
}