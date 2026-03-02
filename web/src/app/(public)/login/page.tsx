import { redirect } from "next/navigation";
import LoginForm from "./LoginForm";
import { getMeServer } from "@/components/auth/server";
import { Card } from "@/components/layout/Card";

export default async function LoginPage() {
  const me = await getMeServer();
  if (me) redirect("/dashboard");
  return <Card background="blob"><LoginForm /></Card>;
}