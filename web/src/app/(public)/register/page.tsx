import { redirect } from "next/navigation";

import { Card } from "@/components/layout/Card";
import { ApiError } from "@/lib/api/errors";
import { getMe } from "@/lib/api/services/auth.browser";

import RegisterForm from "./RegisterForm";

export default async function RegisterPage() {
  try {
    await getMe();
    redirect("/dashboard"); 
  } catch (e) {
    if (!(e instanceof ApiError && e.status === 401)) throw e;
  }

  return <Card background="blob"><RegisterForm /></Card>;
}