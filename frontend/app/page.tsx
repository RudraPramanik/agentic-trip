"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  HitlCandidate,
  HitlPayload,
  getSession,
  postHitlChoice,
  postMessage,
  readSse,
} from "@/lib/sse";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type ChatLine = { role: "user" | "assistant" | "error"; content: string };

function candidateLabel(c: HitlCandidate): string {
  return c.label || c.display_name || c.name || c.choice_id || c.geo_id || "option";
}

function candidateId(c: HitlCandidate): string {
  return c.choice_id || c.geo_id || candidateLabel(c);
}

export default function ChatShell() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState("Starting session…");
  const [input, setInput] = useState("");
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);
  const [hitl, setHitl] = useState<HitlPayload | null>(null);

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

  const refreshSession = useCallback(async (id: string) => {
    const res = await getSession(API_BASE, id);
    if (!res.ok) return;
    const body = (await res.json()) as {
      messages?: { role: string; content: string }[];
      hitl?: HitlPayload | null;
      trip_scope?: { kind?: string; name?: string } | null;
    };
    if (body.messages) {
      setLines(
        body.messages.map((m) => ({
          role: m.role as ChatLine["role"],
          content: m.content,
        })),
      );
    }
    const pending =
      body.hitl && body.hitl.status === "pending" ? body.hitl : null;
    setHitl(pending);
    if (body.trip_scope?.kind) {
      setStatus(
        `Scope locked: ${body.trip_scope.kind} — ${body.trip_scope.name ?? ""}`,
      );
    } else if (pending) {
      setStatus(pending.prompt || "Pick a place to continue");
    }
  }, []);

  const onSubmit = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      if (!sessionId || !input.trim() || busy) return;
      const text = input.trim();
      setInput("");
      setBusy(true);
      setStreaming("");
      setHitl(null);
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
          onHitl: (payload) => {
            setHitl(payload);
            setStatus(payload.prompt || "Pick a place to continue");
          },
        });
        if (assistant && !sawMessage) {
          setLines((prev) => [...prev, { role: "assistant", content: assistant }]);
        }
        await refreshSession(sessionId);
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
    [sessionId, input, busy, refreshSession],
  );

  const onPickChip = useCallback(
    async (choiceId: string) => {
      if (!sessionId || busy) return;
      setBusy(true);
      try {
        const res = await postHitlChoice(API_BASE, sessionId, choiceId);
        if (!res.ok) {
          setLines((prev) => [
            ...prev,
            { role: "error", content: `HITL choice failed: ${res.status}` },
          ]);
          return;
        }
        setHitl(null);
        await refreshSession(sessionId);
      } catch (err) {
        setLines((prev) => [
          ...prev,
          { role: "error", content: `HITL request failed: ${err}` },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [sessionId, busy, refreshSession],
  );

  const chips = hitl?.status === "pending" ? hitl.candidates ?? [] : [];

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
        {chips.length > 0 ? (
          <div className="hitl-chips" role="group" aria-label="Place choices">
            <p className="hitl-prompt">{hitl?.prompt || "Choose one:"}</p>
            {chips.map((c) => {
              const id = candidateId(c);
              return (
                <button
                  key={id}
                  type="button"
                  className="hitl-chip"
                  disabled={busy}
                  onClick={() => onPickChip(id)}
                >
                  {candidateLabel(c)}
                </button>
              );
            })}
          </div>
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
