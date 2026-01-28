import { cookies } from "next/headers";
import type { AuthUser } from "@/lib/api/services/users";

export async function getMeServer(): Promise<AuthUser | null> {
  const cookieStore = await cookies();

  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${encodeURIComponent(value)}`)
    .join("; ");
  const res = await fetch(`${process.env.INTERNAL_API_URL}/auth/me`, {
    headers: cookieHeader ? { cookie: cookieHeader } : undefined,
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as AuthUser;
}
