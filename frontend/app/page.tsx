"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { postMessage, readSse } from "@/lib/sse";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type ChatLine = { role: "user" | "assistant" | "error"; content: string };

export default function ChatShell() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState("Starting session…");
  const [input, setInput] = useState("");
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/sessions`, {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) throw new Error(`create session failed: ${res.status}`);
        const body = (await res.json()) as { session_id: string };
        if (!cancelled) {
          setSessionId(body.session_id);
          setStatus("Ready — send a trip prompt");
        }
      } catch (err) {
        if (!cancelled) {
          setStatus(
            `Could not create session. Is the API running at ${API_BASE}? (${err})`,
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onSubmit = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      if (!sessionId || !input.trim() || busy) return;
      const text = input.trim();
      setInput("");
      setBusy(true);
      setStreaming("");
      setLines((prev) => [...prev, { role: "user", content: text }]);
      let sawMessage = false;
      try {
        const response = await postMessage(API_BASE, sessionId, text);
        let assistant = "";
        await readSse(response, {
          onToken: (chunk) => {
            assistant += chunk;
            setStreaming(assistant);
          },
          onMessage: (content) => {
            sawMessage = true;
            setStreaming("");
            setLines((prev) => [...prev, { role: "assistant", content }]);
          },
          onError: (message) => {
            setStreaming("");
            setLines((prev) => [...prev, { role: "error", content: message }]);
          },
        });
        if (assistant && !sawMessage) {
          setLines((prev) => [...prev, { role: "assistant", content: assistant }]);
        }
      } catch (err) {
        setLines((prev) => [
          ...prev,
          { role: "error", content: `Request failed: ${err}` },
        ]);
      } finally {
        setBusy(false);
        setStreaming("");
      }
    },
    [sessionId, input, busy],
  );

  return (
    <main className="shell">
      <header>
        <h1>agentic-trip</h1>
        <p className="status">{status}</p>
      </header>
      <section className="messages" aria-live="polite">
        {lines.map((line, index) => (
          <p key={`${line.role}-${index}`} className={line.role}>
            <strong>{line.role}:</strong> {line.content}
          </p>
        ))}
        {streaming ? (
          <p className="assistant">
            <strong>assistant:</strong> {streaming}
          </p>
        ) : null}
      </section>
      <form onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. 10 days in Japan, food, slow"
          disabled={!sessionId || busy}
          aria-label="Message"
        />
        <button type="submit" disabled={!sessionId || busy || !input.trim()}>
          Send
        </button>
      </form>
    </main>
  );
}
