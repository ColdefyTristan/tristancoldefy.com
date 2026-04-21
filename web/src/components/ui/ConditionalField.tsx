"use client";

import { Book,BookAlert,BookCheck  } from "lucide-react";
import { useMemo, useState } from "react";

import { Input } from "@/components/ui/Input";

import styles from "./ConditionalField.module.css";

export type Rule = {
  key: string;
  label: string;
  test: (value: string) => boolean;
};

export function isValid(value: string, rules: Rule[], emptyState: "neutral" | "valid" | "invalid" = "neutral") {
  const v = value;
  if (v.length === 0) return emptyState !== "invalid";
  return rules.every((r) => r.test(v));
}

type Props = {
  label?: string;

  value: string;
  onChange: (v: string) => void;

  rules: Rule[];

  // Comportement quand vide
  // - neutral: pas de rouge/vert
  // - valid: considéré OK (utile pour champ optionnel)
  emptyState?: "neutral" | "valid" | "invalid";

  id?: string;
  name?: string;
  type?: React.HTMLInputTypeAttribute; // "text" | "password" | "email" ...
  autoComplete?: string;
  disabled?: boolean;
  className?: string;

  // Icônes (optionnel)
  okIcon?: React.ReactNode;
  koIcon?: React.ReactNode;
  neutralIcon?: React.ReactNode;
};


export function ConditionalField({
  label,
  value,
  onChange,
  rules,
  emptyState = "neutral",
  id,
  name,
  type = "text",
  autoComplete,
  disabled,
  className,
  okIcon,
  koIcon,
  neutralIcon,
}: Props) {

  const inputId = id ?? name ?? `cf-${type}-${label ?? "field"}`.replace(/\s+/g, "-").toLowerCase();
  const inputName = name ?? inputId;
  const [focused, setFocused] = useState(false);
  const [hoverIcon, setHoverIcon] = useState(false);

  const hasTyped = value.length > 0;

  const { checks, isValid } = useMemo(() => {
    const c: Record<string, boolean> = {};
    for (const r of rules) c[r.key] = r.test(value);
    const valid = rules.every((r) => c[r.key]);
    return { checks: c, isValid: valid };
  }, [value, rules]);

  const validationState: "neutral" | "valid" | "invalid" = !hasTyped
    ? emptyState
    : isValid
      ? "valid"
      : "invalid";

  const open = focused || hoverIcon;

  const defaultOk = <BookCheck className={styles.iconOk} />;
  const defaultKo = <BookAlert className={styles.iconKo} />;
  const defaultNeutral = <Book className={styles.iconNeutral} />; 
  const rightIcon = !hasTyped
  ? isValid
    ? neutralIcon ?? defaultNeutral
    : koIcon ?? defaultKo
  : isValid
    ? okIcon ?? defaultOk
    : koIcon ?? defaultKo;
  return (
    <div className={`${styles.wrap} ${className ?? ""}`}>
      <Input
        id={inputId}
        name={inputName}
        label={label}
        type={type}
        autoComplete={autoComplete}
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        validationState={validationState}
        rightSlot={
          <span
            className={styles.icon}
            aria-hidden="true"
            onMouseEnter={() => setHoverIcon(true)}
            onMouseLeave={() => setHoverIcon(false)}
          >
            {rightIcon}
          </span>
        }
      />

      <div
        className={`${styles.bubble} ${open ? styles.open : ""}`}
        aria-hidden={!open}
        onMouseEnter={() => setHoverIcon(true)}
        onMouseLeave={() => setHoverIcon(false)}
      >
        <ul className={styles.list}>
          {rules.map((r) => (
            <RuleRow key={r.key} ok={checks[r.key]} text={r.label} />
          ))}
        </ul>
      </div>
    </div>
  );
}

function RuleRow({ ok, text }: { ok: boolean; text: string }) {
  return (
    <li className={`${styles.rule} ${ok ? styles.ok : styles.ko}`}>
      <span className={styles.dot} aria-hidden="true">
        {ok ? "✓" : "•"}
      </span>
      <span>{text}</span>
    </li>
  );
}
