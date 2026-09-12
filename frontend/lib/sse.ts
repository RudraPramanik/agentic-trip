export async function postMessage(
  apiBase: string,
  sessionId: string,
  text: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}/messages`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function postHitlChoice(
  apiBase: string,
  sessionId: string,
  choiceId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}/hitl`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ choice_id: choiceId }),
  });
}

export async function getSession(
  apiBase: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}`, {
    method: "GET",
    credentials: "include",
  });
}

export async function getCatalog(
  apiBase: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}/catalog`, {
    method: "GET",
    credentials: "include",
  });
}

export async function postCatalogAcquire(
  apiBase: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/catalog/acquire`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function postGenerate(
  apiBase: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}/generate`, {
    method: "POST",
    credentials: "include",
  });
}

export async function postGenerateAbort(
  apiBase: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/sessions/${sessionId}/generate/abort`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getTrip(
  apiBase: string,
  tripId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/trips/${tripId}`, {
    method: "GET",
    credentials: "include",
  });
}

export async function getTripExport(
  apiBase: string,
  tripId: string,
): Promise<Response> {
  return fetch(`${apiBase}/api/v1/trips/${tripId}/export`, {
    method: "GET",
    credentials: "include",
  });
}

export type CatalogReadiness = {
  ready?: boolean;
  status?: string;
  place_count?: number | null;
  error?: string | null;
};

export type DraftItinerary = {
  status?: string;
  days?: { day_index?: number; stops?: { place_id?: string; name?: string }[] }[];
  place_ids?: string[];
};

export type GuidebookExport = {
  trip_id?: string;
  cover?: {
    title?: string;
    status?: string;
    day_count?: number;
    stop_count?: number;
    hubs?: string[];
  };
  hubs?: string[];
  days?: {
    day_index?: number;
    title?: string | null;
    story?: string | null;
    hub_id?: string | null;
    stops?: {
      place_id?: string;
      name?: string;
      lon?: number | null;
      lat?: number | null;
      title?: string | null;
    }[];
  }[];
  narratives?: { day_index?: number; title?: string | null; story?: string | null }[];
  map_points?: {
    place_id?: string;
    name?: string;
    lon?: number;
    lat?: number;
    day_index?: number;
  }[];
  route_geometry?: unknown[];
};

export type HitlCandidate = {
  choice_id?: string;
  geo_id?: string;
  label?: string;
  display_name?: string;
  name?: string;
};

export type HitlPayload = {
  kind?: string;
  status?: string;
  prompt?: string;
  candidates?: HitlCandidate[];
};

export type SseHandlers = {
  onToken?: (text: string) => void;
  onMessage?: (content: string) => void;
  onError?: (message: string) => void;
  onHitl?: (hitl: HitlPayload) => void;
  onProgress?: (stage: string, data: Record<string, unknown>) => void;
  onDone?: (data: Record<string, unknown>) => void;
  onAborted?: (reason: string) => void;
};

/** Read a fetch Response body as SSE (`token` | `message` | `error` | `hitl` | generate events). */
export async function readSse(
  response: Response,
  handlers: SseHandlers,
): Promise<void> {
  if (!response.body) {
    handlers.onError?.("No response body");
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      let dataLine = "";
      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLine = line.slice(5).trim();
        }
      }
      if (!dataLine) continue;
      const data = JSON.parse(dataLine) as Record<string, unknown>;
      if (eventName === "token") {
        handlers.onToken?.(String(data.text ?? ""));
      } else if (eventName === "message") {
        handlers.onMessage?.(String(data.content ?? ""));
      } else if (eventName === "error") {
        handlers.onError?.(String(data.message ?? data.code ?? "error"));
      } else if (eventName === "hitl") {
        handlers.onHitl?.(data as HitlPayload);
      } else if (eventName === "progress") {
        handlers.onProgress?.(String(data.stage ?? ""), data);
      } else if (eventName === "done") {
        handlers.onDone?.(data);
      } else if (eventName === "aborted") {
        handlers.onAborted?.(String(data.reason ?? "aborted"));
      }
    }
  }
}
