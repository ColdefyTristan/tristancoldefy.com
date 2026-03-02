import type { FamilledleAttemptTodayWrapperOut } from "../types";

export async function getTodayAttempt(): Promise<FamilledleAttemptTodayWrapperOut> {
  const res = await fetch("/api/familledle/attempts/today", {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (res.status === 401 || res.status === 403) {
    return { exists: false, attempt: null };
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GET /attempts/today failed (${res.status}): ${text || res.statusText}`);
  }

  return (await res.json()) as FamilledleAttemptTodayWrapperOut;
}