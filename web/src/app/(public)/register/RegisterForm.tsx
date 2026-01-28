"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api/services/auth.browser";
import { ApiError } from "@/lib/api/errors";
import { Button} from "@/components/ui/Button"
import { Input} from "@/components/ui/Input"
import { useToast } from "@/components/ui/Toast";
import { Checkbox } from "@/components/ui/Checkbox";

export default function RegisterForm() {
  const { toast } = useToast();

  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    try {
      await register({ email:email || null ,username, password, remember_me: rememberMe || false });
      router.replace("/dashboard");
      router.refresh(); // utile pour forcer les Server Components à relire la session
    } catch (err) {
      if (err instanceof ApiError) {
        toast({ variant: "error", title: "Error", message: err.message })
      } else {
        // toast({ title: "Login failed", description: "Unexpected error." })
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit}>
        <Input value={username} onChange={(e) => setUsername(e.target.value)} label="Username"/>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} label="Email"/>
        <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} label="Password" />
        <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} label="Remember me"/>
        <Button type="submit" disabled={pending}>{pending ? "..." : "Register"}</Button>

    </form>
  );
}
