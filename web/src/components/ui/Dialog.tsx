"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import styles from "./Dialog.module.css";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className={styles.overlay} />
      <DialogPrimitive.Content className={styles.content}>
        {title ? <DialogPrimitive.Title className={styles.title}>{title}</DialogPrimitive.Title> : null}
        <div className={styles.body}>{children}</div>
        <DialogPrimitive.Close className={styles.closeBtn} aria-label="Close">
          ✕
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
