// app/providers.tsx
"use client";

import React from "react";

import { AuthProvider} from "@/components/auth/AuthProvider";
import { ToastProvider } from "@/components/ui/Toast";
import { AuthUser } from "@/lib/api/services/users";

export function Providers({
  initialUser,
  children,
}: {
  initialUser: AuthUser | null;
  children: React.ReactNode;
}) {
  return (
    <ToastProvider>
      <AuthProvider initialUser={initialUser}>{children}</AuthProvider>
    </ToastProvider>
  );
}
