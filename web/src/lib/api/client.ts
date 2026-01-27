import { ApiError } from "./errors";

type ServerErrorPayload = { code: string; message: string; fields?: Record<string, string[]> };

function isServerErrorPayload(x: unknown): x is ServerErrorPayload {
  return (
    !!x &&
    typeof x === "object" &&
    typeof (x as any).code === "string" &&
    typeof (x as any).message === "string"
  );
}

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type RequestOptions = {
  method: HttpMethod;
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
  timeoutMs?: number;
  signal?: AbortSignal;
} & Omit<RequestInit, "method" | "body" | "headers" | "signal" | "credentials">;

const DEFAULT_TIMEOUT = 10_000;

function getBaseUrl() {
  const raw =
    typeof window === "undefined"
      ? process.env.INTERNAL_API_URL
      : "/api";

  if (!raw) throw new Error("INTERNAL_API_URL is missing (server-side).");
  return raw.replace(/\/$/, "");
}

type ApiErrorLike = {
  status?: number;
  code: string;
  message: string;
  fields?: Record<string, string[]>;
  details?: unknown;
};

function makeError(e: ApiError | ApiErrorLike): ApiError {
  return e instanceof ApiError ? e : new ApiError(e);
}

async function parseBody(res: Response) {
  if (res.status === 204) return null;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try { return await res.json(); }
    catch { throw makeError({ code: "INVALID_RESPONSE", status: res.status, message: "Réponse invalide.", details: "Invalid JSON" }); }
  }

  const text = await res.text().catch(() => "");
  return text || null;
}

function mapHttpError(status: number, payload: unknown): ApiError {
  if (isServerErrorPayload(payload)) {
    return new ApiError({
      status,
      code: payload.code,       
      message: payload.message, 
      fields: payload.fields,
      details: payload,
    });
  }

  if (status === 401)
    return new ApiError({ code: "UNAUTHORIZED", status, message: "Session expired. Please reconnect.", details: payload });

  if (status === 403)
    return new ApiError({ code: "FORBIDDEN", status, message: "Access denied.", details: payload });

  if (status === 404)
    return new ApiError({ code: "NOT_FOUND", status, message: "Resource not found.", details: payload });

  if (status === 422)
    return new ApiError({ code: "VALIDATION_ERROR", status, message: "Invalid fields.", details: payload });

  if (status >= 500)
    return new ApiError({ code: "SERVER_ERROR", status, message: "Server error. Please try again later.", details: payload });

  if (status >= 400)
    return new ApiError({ code: "BAD_REQUEST", status, message: "Invalid request.", details: payload });

  return new ApiError({ code: "UNKNOWN", status, message: "Unknown error.", details: payload });
}

export async function request<T>(opts: RequestOptions): Promise<T> {
  const baseUrl = getBaseUrl();
  
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT;
  const {
  path,
  method,
  body,
  headers,
  signal: externalSignal,
  ...fetchInit
} = opts;


  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort("timeout"), timeoutMs);

  if (opts.signal) {
    opts.signal.addEventListener("abort", () => controller.abort("aborted"), { once: true });
  }

  try {
    const res = await fetch(`${baseUrl}${opts.path}`, {
      ...fetchInit,
      method,
      credentials: "include", // cookies httpOnly
      headers: {
        "Accept": "application/json",
        ...(body != null ? { "Content-Type": "application/json" } : {}),
        ...(headers ?? {}),
      },
      body: body != null ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });


    const payload = await parseBody(res);

    if (!res.ok) throw makeError(mapHttpError(res.status, payload));
    return payload as T;
  } catch (err: any) {
    if (err?.code && err?.message) throw err as ApiError;

    if (err?.name === "AbortError") {
      const reason = controller.signal.reason;
      if (reason === "timeout") throw makeError({ code: "TIMEOUT", message: "Request timed out. Check your connection." });
      throw makeError({ code: "ABORTED", message: "Request cancelled." });
    }

    throw makeError({ code: "NETWORK_ERROR", message: "Unable to reach the server. Check your connection.", details: String(err) });
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = {
  get:  <T>(path: string, o?: Omit<RequestOptions, "method"|"path">) => request<T>({ method: "GET", path, ...o }),
  post: <T>(path: string, body?: unknown, o?: Omit<RequestOptions, "method"|"path"|"body">) => request<T>({ method: "POST", path, body, ...o }),
  put:  <T>(path: string, body?: unknown, o?: Omit<RequestOptions, "method"|"path"|"body">) => request<T>({ method: "PUT", path, body, ...o }),
  patch:<T>(path: string, body?: unknown, o?: Omit<RequestOptions, "method"|"path"|"body">) => request<T>({ method: "PATCH", path, body, ...o }),
  del:  <T>(path: string, o?: Omit<RequestOptions, "method"|"path">) => request<T>({ method: "DELETE", path, ...o }),
};
