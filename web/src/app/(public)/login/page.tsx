import { redirect } from "next/navigation";

import { getMeServer } from "@/components/auth/server";
import { Card } from "@/components/layout/Card";

import LoginForm from "./LoginForm";

export default async function LoginPage() {
  const me = await getMeServer();
  if (me) redirect("/dashboard");
  return <Card background="blob"><LoginForm /></Card>;
}