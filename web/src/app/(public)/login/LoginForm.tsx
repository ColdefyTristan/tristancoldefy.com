"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/errors";
import { Button} from "@/components/ui/Button"
import { Input} from "@/components/ui/Input"
import { useToast } from "@/components/ui/Toast";
import { Checkbox } from "@/components/ui/Checkbox";
import { useAuth } from "@/components/auth/AuthProvider";
export default function LoginForm() {
  const { login } = useAuth();
  

  const { toast } = useToast();

  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    try {
      await login({ identifier, password, remember_me: rememberMe || false });
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
      <Input value={identifier} onChange={(e) => setIdentifier(e.target.value)} label="Username/Email"/> 
      <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} label="Password"/> 
      <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} label="Remember me"/>
      <Button type="submit" disabled={pending}>{pending ? "..." : "Login"}</Button> 
    </form>
  );
}
