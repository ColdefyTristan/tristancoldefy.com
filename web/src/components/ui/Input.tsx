import styles from "./Input.module.css";

type Props = Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> & {
  label?: string;
  hint?: string;
  error?: string;
  validationState?: "neutral" | "valid" | "invalid";
  rightSlot?: React.ReactNode;
};

export function Input({
  label,
  hint,
  error,
  id,
  className,
  validationState,
  rightSlot,
  ...rest
}: Props) {
  const inputId = id ?? rest.name; // fallback propre
  const hintId = hint && inputId ? `${inputId}-hint` : undefined;
  const errorId = error && inputId ? `${inputId}-error` : undefined;

  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`${styles.field} ${validationState ? styles[validationState] : ""}`}>
      {label && inputId ? (
        <label className={styles.label} htmlFor={inputId}>
          {label}
        </label>
      ) : null}

      <input
        {...rest}
        id={inputId}
        className={[
          styles.input,
          error ? styles.inputError : "",
          className ?? "",
        ].join(" ")}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy}
      />

      {rightSlot ? <div className={styles.rightSlot}>{rightSlot}</div> : null}

      {hint ? (
        <div className={styles.hint} id={hintId}>
          {hint}
        </div>
      ) : null}

      {error ? (
        <div className={styles.error} id={errorId}>
          {error}
        </div>
      ) : null}
    </div>
  );
}
