import { redirect } from "next/navigation";
import { getMe } from "@/lib/api/services/auth.browser";
import { ApiError } from "@/lib/api/errors";
import RegisterForm from "./RegisterForm";
import { Card } from "@/components/layout/Card";

export default async function RegisterPage() {
  try {
    await getMe();
    redirect("/dashboard"); 
  } catch (e) {
    if (!(e instanceof ApiError && e.status === 401)) throw e;
  }

  return <Card background="blob"><RegisterForm /></Card>;
}