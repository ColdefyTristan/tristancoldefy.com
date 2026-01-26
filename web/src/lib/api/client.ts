import type { ApiError } from "./errors";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type RequestOptions = {
  method: HttpMethod;
  path: string;
  body?: unknown;
  headers?: Record<string, string>;
  timeoutMs?: number;
  signal?: AbortSignal;
};

const DEFAULT_TIMEOUT = 10_000;

function getBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "/api";
}

function makeError(e: ApiError): ApiError {
  return e;
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
  if (status === 401) return { code: "UNAUTHORIZED", status, message: "Session expirée. Merci de vous reconnecter.", details: payload };
  if (status === 403) return { code: "FORBIDDEN", status, message: "Accès refusé.", details: payload };
  if (status === 404) return { code: "NOT_FOUND", status, message: "Ressource introuvable.", details: payload };
  if (status >= 500) return { code: "SERVER_ERROR", status, message: "Erreur serveur. Réessayez plus tard.", details: payload };
  if (status >= 400) return { code: "BAD_REQUEST", status, message: "Requête invalide.", details: payload };
  return { code: "UNKNOWN", status, message: "Erreur inconnue.", details: payload };
}

export async function request<T>(opts: RequestOptions): Promise<T> {
  const baseUrl = getBaseUrl();
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort("timeout"), timeoutMs);

  if (opts.signal) {
    opts.signal.addEventListener("abort", () => controller.abort("aborted"), { once: true });
  }

  try {
    const res = await fetch(`${baseUrl}${opts.path}`, {
      method: opts.method,
      credentials: "include", // cookies httpOnly
      headers: {
        "Accept": "application/json",
        ...(opts.body ? { "Content-Type": "application/json" } : {}),
        ...(opts.headers ?? {}),
      },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      signal: controller.signal,
    });

    const payload = await parseBody(res);

    if (!res.ok) throw makeError(mapHttpError(res.status, payload));
    return payload as T;
  } catch (err: any) {
    if (err?.code && err?.message) throw err as ApiError;

    if (err?.name === "AbortError") {
      const reason = controller.signal.reason;
      if (reason === "timeout") throw makeError({ code: "TIMEOUT", message: "Délai dépassé. Vérifiez votre connexion." });
      throw makeError({ code: "ABORTED", message: "Requête annulée." });
    }

    throw makeError({ code: "NETWORK_ERROR", message: "Impossible de contacter le serveur. Vérifiez votre connexion.", details: String(err) });
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
