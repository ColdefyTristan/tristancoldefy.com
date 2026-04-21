"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Button} from "@/components/ui/Button"
import { Checkbox } from "@/components/ui/Checkbox";
import { Input} from "@/components/ui/Input"
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/errors";

import styles from "./LoginForm.module.css";

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
    <form className={styles.form} onSubmit={onSubmit}>
      <Input value={identifier} onChange={(e) => setIdentifier(e.target.value)} name={"identifier"} label="Username/Email"/> 
      <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} name={"password"} label="Password"/> 
      <div className={styles.actions}>
        <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} label="Remember me"/>
        <Button type="submit" variant="secondary" disabled={pending}>{pending ? "..." : "Login"}</Button> 
      </div>
    </form>
  );
}
