import { redirect } from "next/navigation";
import { getMe } from "@/lib/api/services/auth";
import { ApiError } from "@/lib/api/errors"; 

export const dynamic = "force-dynamic";

export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  try {
    await getMe(); 
    return <>{children}</>;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) redirect("/login");
    throw e;
  }
}
