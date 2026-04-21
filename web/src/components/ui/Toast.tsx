"use client";

import * as ToastPrimitive from "@radix-ui/react-toast";
import React from "react";

import styles from "./Toast.module.css";

type ToastVariant = "info" | "success" | "error";

type ToastItem = {
  id: string;
  variant: ToastVariant;
  title?: string;
  message: string;
  durationMs?: number;
};

type ToastInput = Omit<ToastItem, "id">;

type ToastContextValue = {
  toast: (t: ToastInput) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ToastItem[]>([]);

  const toast = React.useCallback((t: ToastInput) => {
    const id = crypto.randomUUID();
    setItems((prev) => [{ id, ...t }, ...prev].slice(0, 5));
  }, []);

  const remove = React.useCallback((id: string) => {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}

        {items.map((t) => (
          <ToastPrimitive.Root
            key={t.id}
            className={[styles.toast, styles[t.variant]].join(" ")}
            duration={t.durationMs ?? 3500}
            onOpenChange={(open) => {
              if (!open) remove(t.id);
            }}
          >
            {t.title ? (
              <ToastPrimitive.Title className={styles.title}>
                {t.title}
              </ToastPrimitive.Title>
            ) : null}

            <ToastPrimitive.Description className={styles.message}>
              {t.message}
            </ToastPrimitive.Description>

            <ToastPrimitive.Close className={styles.close} aria-label="Close">
              ✕
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}

        <ToastPrimitive.Viewport className={styles.viewport} />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
