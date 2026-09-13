"use client";

import dynamic from "next/dynamic";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { GuidebookView } from "@/components/guidebook-view";
import {
  CatalogReadiness,
  DraftItinerary,
  GuidebookExport,
  HitlCandidate,
  HitlPayload,
  getCatalog,
  getSession,
  getTripExport,
  postCatalogAcquire,
  postGenerate,
  postGenerateAbort,
  postHitlChoice,
  postMessage,
  postRevise,
  readSse,
} from "@/lib/sse";

const TripMap = dynamic(
  () => import("@/components/trip-map").then((m) => m.TripMap),
  { ssr: false },
);

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
  const [tripScope, setTripScope] = useState<{
    kind?: string;
    name?: string;
  } | null>(null);
  const [catalog, setCatalog] = useState<CatalogReadiness | null>(null);
  const [draft, setDraft] = useState<DraftItinerary | null>(null);
  const [tripId, setTripId] = useState<string | null>(null);
  const [guidebook, setGuidebook] = useState<GuidebookExport | null>(null);
  const [showGuidebook, setShowGuidebook] = useState(false);
  const [mapFailed, setMapFailed] = useState(false);
  const [generateBusy, setGenerateBusy] = useState(false);
  const [generateStage, setGenerateStage] = useState<string | null>(null);
  const [reviseBusy, setReviseBusy] = useState(false);
  const [reviseStage, setReviseStage] = useState<string | null>(null);

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

  const loadGuidebook = useCallback(async (id: string) => {
    const res = await getTripExport(API_BASE, id);
    if (!res.ok) return;
    const body = (await res.json()) as GuidebookExport;
    setGuidebook(body);
    setMapFailed(false);
    setShowGuidebook(true);
  }, []);

  const refreshSession = useCallback(async (id: string) => {
    const res = await getSession(API_BASE, id);
    if (!res.ok) return;
    const body = (await res.json()) as {
      messages?: { role: string; content: string }[];
      hitl?: HitlPayload | null;
      trip_scope?: { kind?: string; name?: string } | null;
      catalog?: CatalogReadiness | null;
      itinerary?: DraftItinerary | null;
      trip_id?: string | null;
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
    setTripScope(body.trip_scope ?? null);
    if (body.catalog) {
      setCatalog(body.catalog);
    }
    if (body.itinerary) {
      setDraft(body.itinerary);
    }
    if (body.trip_id) {
      setTripId(body.trip_id);
    }
    if (body.trip_scope?.kind) {
      const cat = body.catalog?.status
        ? ` · catalog: ${body.catalog.status}`
        : "";
      const draftNote =
        body.itinerary?.status === "draft"
          ? ` · draft: ${body.itinerary.days?.length ?? 0} days`
          : "";
      const tripNote = body.trip_id ? ` · trip: ${body.trip_id.slice(0, 8)}…` : "";
      setStatus(
        `Scope locked: ${body.trip_scope.kind} — ${body.trip_scope.name ?? ""}${cat}${draftNote}${tripNote}`,
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

  const onAcquireCatalog = useCallback(async () => {
    if (!sessionId || busy) return;
    setBusy(true);
    try {
      const res = await postCatalogAcquire(API_BASE, sessionId);
      if (!res.ok) {
        setLines((prev) => [
          ...prev,
          { role: "error", content: `Catalog acquire failed: ${res.status}` },
        ]);
        return;
      }
      const body = (await res.json()) as { status?: string };
      setStatus(`Catalog acquire: ${body.status ?? "enqueued"}`);
      const cat = await getCatalog(API_BASE, sessionId);
      if (cat.ok) {
        const readiness = (await cat.json()) as CatalogReadiness;
        setCatalog(readiness);
        setStatus(
          `Catalog: ${readiness.status ?? "unknown"}` +
            (readiness.place_count != null
              ? ` (${readiness.place_count} places)`
              : ""),
        );
      }
      await refreshSession(sessionId);
    } catch (err) {
      setLines((prev) => [
        ...prev,
        { role: "error", content: `Catalog acquire error: ${err}` },
      ]);
    } finally {
      setBusy(false);
    }
  }, [sessionId, busy, refreshSession]);

  const onBuildPlan = useCallback(async () => {
    if (!sessionId || busy || generateBusy || reviseBusy) return;
    setGenerateBusy(true);
    setGenerateStage("starting");
    setStatus("Building plan…");
    try {
      const response = await postGenerate(API_BASE, sessionId);
      await readSse(response, {
        onProgress: (stage) => {
          setGenerateStage(stage);
          setStatus(`Generating: ${stage}`);
        },
        onDone: (data) => {
          setGenerateStage("done");
          setStatus("Draft ready");
          const tid = typeof data.trip_id === "string" ? data.trip_id : null;
          if (tid) {
            setTripId(tid);
          }
        },
        onAborted: (reason) => {
          setGenerateStage(null);
          setStatus(`Generate aborted: ${reason}`);
          setLines((prev) => [
            ...prev,
            { role: "error", content: `Generate aborted: ${reason}` },
          ]);
        },
        onError: (message) => {
          setGenerateStage(null);
          setStatus(`Generate failed: ${message}`);
          setLines((prev) => [
            ...prev,
            { role: "error", content: `Generate failed: ${message}` },
          ]);
        },
      });
      await refreshSession(sessionId);
    } catch (err) {
      setLines((prev) => [
        ...prev,
        { role: "error", content: `Generate request failed: ${err}` },
      ]);
    } finally {
      setGenerateBusy(false);
    }
  }, [sessionId, busy, generateBusy, reviseBusy, refreshSession]);

  const onAbortGenerate = useCallback(async () => {
    if (!sessionId) return;
    try {
      await postGenerateAbort(API_BASE, sessionId);
      setStatus("Abort requested…");
    } catch (err) {
      setLines((prev) => [
        ...prev,
        { role: "error", content: `Abort failed: ${err}` },
      ]);
    }
  }, [sessionId]);

  const onRevisePlan = useCallback(async () => {
    if (!sessionId || !input.trim() || busy || generateBusy || reviseBusy) return;
    const text = input.trim();
    setInput("");
    setLines((prev) => [...prev, { role: "user", content: text }]);
    setReviseBusy(true);
    setReviseStage("starting");
    setStatus("Revising plan…");
    const previousDraft = draft;
    const previousGuidebook = guidebook;
    let succeeded = false;
    let doneTripId: string | null = null;
    try {
      const response = await postRevise(API_BASE, sessionId, text);
      await readSse(response, {
        onProgress: (stage) => {
          setReviseStage(stage);
          setStatus(`Revising: ${stage}`);
        },
        onDone: (data) => {
          succeeded = true;
          setReviseStage("done");
          setStatus("Draft updated");
          const tid = typeof data.trip_id === "string" ? data.trip_id : null;
          if (tid) {
            doneTripId = tid;
            setTripId(tid);
          }
        },
        onAborted: (reason) => {
          setReviseStage(null);
          setStatus(`Revise aborted: ${reason}`);
          setLines((prev) => [
            ...prev,
            { role: "error", content: `Revise aborted: ${reason}` },
          ]);
          if (previousDraft) setDraft(previousDraft);
          if (previousGuidebook) setGuidebook(previousGuidebook);
        },
        onError: (message) => {
          setReviseStage(null);
          setStatus(`Revise failed: ${message}`);
          setLines((prev) => [
            ...prev,
            { role: "error", content: `Revise failed: ${message}` },
          ]);
          if (previousDraft) setDraft(previousDraft);
          if (previousGuidebook) setGuidebook(previousGuidebook);
        },
      });
      if (succeeded) {
        await refreshSession(sessionId);
        const sess = await getSession(API_BASE, sessionId);
        if (sess.ok) {
          const body = (await sess.json()) as { trip_id?: string | null };
          const tid = body.trip_id || doneTripId;
          if (tid) {
            setTripId(tid);
            await loadGuidebook(tid);
          }
        } else if (doneTripId) {
          await loadGuidebook(doneTripId);
        }
      }
    } catch (err) {
      setLines((prev) => [
        ...prev,
        { role: "error", content: `Revise request failed: ${err}` },
      ]);
      if (previousDraft) setDraft(previousDraft);
      if (previousGuidebook) setGuidebook(previousGuidebook);
    } finally {
      setReviseBusy(false);
    }
  }, [
    sessionId,
    input,
    busy,
    generateBusy,
    reviseBusy,
    draft,
    guidebook,
    refreshSession,
    loadGuidebook,
  ]);

  const chips = hitl?.status === "pending" ? hitl.candidates ?? [] : [];
  const showAcquire = Boolean(tripScope?.kind) && !hitl;
  const showBuildPlan = Boolean(tripScope?.kind) && !hitl;
  const canOpenGuidebook = Boolean(tripId) && draft?.status === "draft";
  const showRevisePlan = Boolean(draft?.status === "draft") && !hitl;
  const expensiveBusy = busy || generateBusy || reviseBusy;

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
        {showAcquire ? (
          <div className="catalog-panel" role="group" aria-label="Catalog">
            <p className="catalog-status">
              Catalog: {catalog?.status ?? "not started"}
              {catalog?.place_count != null
                ? ` · ${catalog.place_count} places`
                : ""}
            </p>
            <button
              type="button"
              className="catalog-acquire"
              disabled={expensiveBusy}
              onClick={() => onAcquireCatalog()}
            >
              Acquire places
            </button>
          </div>
        ) : null}
        {showBuildPlan ? (
          <div className="generate-panel" role="group" aria-label="Build plan">
            <p className="generate-status">
              {draft?.status === "draft"
                ? `Draft: ${draft.days?.length ?? 0} days · ${draft.place_ids?.length ?? 0} stops`
                : generateStage
                  ? `Generate: ${generateStage}`
                  : "Ready to build a plan (does not start on chat send)"}
            </p>
            <button
              type="button"
              className="build-plan"
              data-testid="build-plan-btn"
              disabled={expensiveBusy}
              onClick={() => onBuildPlan()}
            >
              Build plan
            </button>
            {generateBusy || reviseBusy ? (
              <button
                type="button"
                className="generate-abort"
                data-testid="abort-run-btn"
                onClick={() => onAbortGenerate()}
              >
                Abort
              </button>
            ) : null}
            {canOpenGuidebook ? (
              <button
                type="button"
                className="open-guidebook"
                disabled={busy}
                onClick={() => tripId && loadGuidebook(tripId)}
              >
                Open guidebook
              </button>
            ) : null}
          </div>
        ) : null}
        {showRevisePlan ? (
          <div className="revise-panel" role="group" aria-label="Revise plan">
            <p className="generate-status" data-testid="revise-status">
              {reviseStage
                ? `Revise: ${reviseStage}`
                : "Revise plan uses the composer text (Send stays chat-only)"}
            </p>
            <button
              type="button"
              className="revise-plan"
              data-testid="revise-plan-btn"
              disabled={expensiveBusy || !input.trim()}
              onClick={() => onRevisePlan()}
            >
              Revise plan
            </button>
          </div>
        ) : null}
        {showGuidebook && guidebook ? (
          <GuidebookView
            exportData={guidebook}
            mapSlot={
              mapFailed ? undefined : (
                <TripMap
                  exportData={guidebook}
                  onStyleFail={() => setMapFailed(true)}
                />
              )
            }
          />
        ) : null}
        {showGuidebook && mapFailed ? (
          <p className="map-fallback" role="status">
            Map unavailable — guidebook list remains usable.
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
        <button
          type="submit"
          data-testid="chat-send-btn"
          disabled={!sessionId || expensiveBusy || !input.trim()}
        >
          Send
        </button>
      </form>
    </main>
  );
}
