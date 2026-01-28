"use client";

import React, { createContext, useContext, useMemo, useState } from "react";
import { getMe } from "@/lib/api/services/auth.browser";
import { ApiError } from "@/lib/api/errors"; 
import {AuthUser} from "@/lib/api/services/users"
import { logout as apiLogout, login as apiLogin } from "@/lib/api/services/auth.browser";
import { useRouter } from "next/navigation";
import { LoginRequest } from "@/lib/api/services/auth.browser";

export type AuthStatus = "authenticated" | "guest";

type AuthContextValue = {
  user: AuthUser | null;
  status: AuthStatus;
  setUser: (user: AuthUser | null) => void;
  refreshMe: () => Promise<AuthUser | null>;
  logout: () => Promise<void>;
  login: (body:LoginRequest) => Promise<void>
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  initialUser,
  children,
}: {
  initialUser: AuthUser | null;
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(initialUser);

  const status: AuthStatus = user ? "authenticated" : "guest";

  const router = useRouter();

  async function refreshMe(): Promise<AuthUser | null> {
    try {
      const me = await getMe();
      setUser(me);
      return me;
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setUser(null);
        return null;
      }
      throw e;
    }
  }
  
  async function logout(): Promise<void> {
    await apiLogout();
    setUser(null);
    router.refresh(); 
  }

  async function login(body : LoginRequest): Promise<void> {
    await apiLogin(body);
    await refreshMe();
    router.refresh(); 
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, setUser, refreshMe, logout, login }),
    [user, status]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
