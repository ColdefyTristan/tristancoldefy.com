export type ClientErrorCode = "NETWORK_ERROR" | "TIMEOUT" | "ABORTED";
export type ApiErrorCode = ClientErrorCode | string;

export type ApiValidationFields = Record<string, string[]>;

export class ApiError extends Error {
  status?: number;
  code: ApiErrorCode;
  fields?: ApiValidationFields;
  details?: unknown;

  constructor(args: {
    code: ApiErrorCode;
    message: string;
    status?: number;
    fields?: ApiValidationFields;
    details?: unknown;
  }) {
    super(args.message);
    this.name = "ApiError";
    this.code = args.code;
    this.status = args.status;
    this.fields = args.fields;
    this.details = args.details;
  }

  // Optionnel: pour garder un affichage JSON propre si tu logs l'objet
  toJSON() {
    return {
      name: this.name,
      status: this.status,
      code: this.code,
      message: this.message,
      fields: this.fields,
      details: this.details,
    };
  }
}

export function isApiError(e: unknown): e is ApiError {
  return e instanceof ApiError;
}
