"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api/services/auth.browser";
import { ApiError } from "@/lib/api/errors";
import { Button} from "@/components/ui/Button"
import { Input} from "@/components/ui/Input"
import { useToast } from "@/components/ui/Toast";
import { Checkbox } from "@/components/ui/Checkbox";
import { ConditionalField,isValid } from "@/components/ui/ConditionalField";
import { passwordRules, usernameRules, emailRulesOptional } from "@/lib/fieldRules";
import styles from "./RegisterForm.module.css"
export default function RegisterForm() {
  const { toast } = useToast();

  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [pending, setPending] = useState(false);

  const usernameOk = isValid(username, usernameRules, "invalid"); 
  const passwordOk = isValid(password, passwordRules, "invalid");
  const emailOk = isValid(email, emailRulesOptional, "valid");    
  const canSubmit = usernameOk && passwordOk && emailOk && !pending;

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
    <form className={styles.form} onSubmit={onSubmit}>
        
      <ConditionalField
        label="Username"
        value={username}
        onChange={setUsername}
        rules={usernameRules}
        type="text"
        autoComplete="username"
        emptyState="neutral"
      />

      <ConditionalField
        label="Email (optional)"
        value={email}
        onChange={setEmail}
        rules={emailRulesOptional}
        type="email"
        autoComplete="email"
        emptyState="neutral"
      />

      <ConditionalField
        label="Password"
        value={password}
        onChange={setPassword}
        rules={passwordRules}
        type="password"
        autoComplete="new-password"
      />
        <div className={styles.actions}>

          <Checkbox checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} label="Remember me"/>
          <Button variant="secondary" type="submit" disabled={pending || !canSubmit}>{pending ? "..." : "Register"}</Button>
        </div>
    </form>
  );
}
