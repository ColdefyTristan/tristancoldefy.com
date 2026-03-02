import type { BrowserAnim, StepId } from "./types";

export type Step<T> = {
  id: StepId;
  durationMs: number;
  from: T;
  to: T;
};

export const BROWSER_STEPS: Step<BrowserAnim>[] = [
  {
    id: "browser.cursor_to_dot",
    durationMs: 650,
    from: { cursorX: 60, cursorY: 52, cardOpen: 0, dotAlpha: 1 },
    to: { cursorX: 28, cursorY: 40, cardOpen: 0, dotAlpha: 1 },
  },
  {
    id: "browser.dot_expand_to_card",
    durationMs: 520,
    from: { cursorX: 28, cursorY: 40, cardOpen: 0, dotAlpha: 1 },
    to: { cursorX: 28, cursorY: 40, cardOpen: 1, dotAlpha: 0 },
  },
  {
    id: "browser.hold_open",
    durationMs: 380,
    from: { cursorX: 28, cursorY: 40, cardOpen: 1, dotAlpha: 0 },
    to: { cursorX: 28, cursorY: 40, cardOpen: 1, dotAlpha: 0 },
  },
  {
    id: "browser.cursor_to_center",
    durationMs: 650,
    from: { cursorX: 28, cursorY: 40, cardOpen: 1, dotAlpha: 0 },
    to: { cursorX: 60, cursorY: 52, cardOpen: 1, dotAlpha: 0 },
  },
  {
    id: "browser.reset",
    durationMs: 350,
    from: { cursorX: 60, cursorY: 52, cardOpen: 1, dotAlpha: 0 },
    to: { cursorX: 60, cursorY: 52, cardOpen: 0, dotAlpha: 1 },
  },
];