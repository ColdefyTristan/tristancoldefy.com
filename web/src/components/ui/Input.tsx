import styles from "./Input.module.css";

type Props = Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> & {
  label?: string;
  hint?: string;
  error?: string;
};

export function Input({ label, hint, error, id, className, ...rest }: Props) {
  const inputId = id ;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;

  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={styles.field}>
      {label ? (
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
