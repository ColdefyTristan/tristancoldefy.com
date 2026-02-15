import type { Rule } from "@/components/ui/ConditionalField";

export const passwordRules: Rule[] = [
  { key: "length", label: "8–128 characters", test: (v) => v.length >= 8 && v.length <= 128 },
  { key: "lowercase", label: "At least 1 lowercase letter", test: (v) => /[a-z]/.test(v) },
  { key: "uppercase", label: "At least 1 uppercase letter", test: (v) => /[A-Z]/.test(v) },
  { key: "digit", label: "At least 1 digit", test: (v) => /\d/.test(v) },
  { key: "symbol", label: "At least 1 symbol", test: (v) => /[^a-zA-Z0-9]/.test(v) },
];

export const usernameRules: Rule[] = [
  { key: "length", label: "3–25 characters", test: (v) => v.trim().length >= 3 && v.trim().length <= 25 },
  { key: "charset", label: "Only letters, digits, underscore", test: (v) => /^[a-zA-Z0-9_]+$/.test(v.trim()) },
];

export const emailRulesOptional: Rule[] = [
  {
    key: "email",
    label: "Valid email format (optional)",
    test: (v) => v.trim() === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()),
  },
];
