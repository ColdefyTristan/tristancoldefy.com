import { api } from "../client";
import { endpoints } from "../endpoints";

export type Me = { id: string; email: string };

export function getMe() {
  return api.get<Me | null>(endpoints.me);
}
