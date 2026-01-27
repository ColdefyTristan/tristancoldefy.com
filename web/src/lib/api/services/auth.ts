import { api } from "../client";
import { endpoints } from "../endpoints";

export type Me = { id: string; username: string; email?: string | null };

export async function getMe(): Promise<Me> {
  return api.get<Me>("/auth/me", { cache: "no-store" });
}