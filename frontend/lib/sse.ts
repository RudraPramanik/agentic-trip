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

export type SseHandlers = {
  onToken?: (text: string) => void;
  onMessage?: (content: string) => void;
  onError?: (message: string) => void;
};

/** Read a fetch Response body as SSE (`token` | `message` | `error`). */
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
      const data = JSON.parse(dataLine) as Record<string, string>;
      if (eventName === "token") {
        handlers.onToken?.(data.text ?? "");
      } else if (eventName === "message") {
        handlers.onMessage?.(data.content ?? "");
      } else if (eventName === "error") {
        handlers.onError?.(data.message ?? "error");
      }
    }
  }
}
