import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

import type { ClueType, RiftdleAttemptTodayWrapperOut } from "../types";

export async function getTodayAttempt(): Promise<RiftdleAttemptTodayWrapperOut> {
  try {
    return await api.get<RiftdleAttemptTodayWrapperOut>("/riftdle/attempts/today", {
      cache: "no-store",
    });
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
      return { exists: false, attempt: null };
    }
    throw e;
  }
}

export async function postClue(clue: ClueType): Promise<void> {
  try {
    await api.post("/riftdle/attempts/clue", { clue });
  } catch (e) {
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) return;
    throw e;
  }
}
