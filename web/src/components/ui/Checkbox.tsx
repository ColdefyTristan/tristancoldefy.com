import * as React from "react";

import styles from "./Checkbox.module.css";

type Props = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label?: React.ReactNode;
  variant?: "primary" | "secondary";
};

export function Checkbox({
  id,
  label,
  variant = "secondary",
  disabled,
  className,
  ...rest
}: Props) {
  const autoId = React.useId();
  const inputId = id ?? autoId;

  return (
    <label
      htmlFor={inputId}
      className={[
        styles.root,
        variant === "primary" ? styles.primary : styles.secondary,
        disabled ? styles.disabled : "",
        className ?? "",
      ].join(" ")}
    >
      <input
        {...rest}
        id={inputId}
        type="checkbox"
        disabled={disabled}
        className={styles.input}
      />
      <span className={styles.box} aria-hidden="true" />
      {label != null ? <span className={styles.label}>{label}</span> : null}
    </label>
  );
}
