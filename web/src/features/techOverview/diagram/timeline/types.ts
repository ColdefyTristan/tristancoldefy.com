export type NodeKey = "browser" | "proxy" | "next" | "api" | "db" | "flow";
export type StepId = `${NodeKey}.${string}`;

export type BrowserAnim = {
  cursorX: number;
  cursorY: number;
  cardOpen: number; // 0..1
  dotAlpha: number; // 0..1
};

export type DiagramAnimState = {
  browser: BrowserAnim;
  played: boolean;
  reduceMotion: boolean;
};