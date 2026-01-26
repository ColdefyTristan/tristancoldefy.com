export type ApiErrorCode =
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | "ABORTED"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "SERVER_ERROR"
  | "BAD_REQUEST"
  | "INVALID_RESPONSE"
  | "UNKNOWN";

export type ApiError = {
  code: ApiErrorCode;
  status?: number;
  message: string;      // user-friendly
  details?: unknown;    // debug / payload
};
