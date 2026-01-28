import { redirect } from "next/navigation";
import { getMe } from "@/lib/api/services/auth.browser";
import { ApiError } from "@/lib/api/errors";
import RegisterForm from "./RegisterForm";

export default async function RegisterPage() {
  try {
    await getMe();
    redirect("/dashboard"); // déjà connecté → zone protégée
  } catch (e) {
    // IMPORTANT: on ignore uniquement le cas "pas connecté"
    if (!(e instanceof ApiError && e.status === 401)) throw e;
  }

  return <RegisterForm />;
}