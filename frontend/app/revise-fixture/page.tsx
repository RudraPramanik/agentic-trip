"use client";

import { FormEvent, useState } from "react";

import { GuidebookView } from "@/components/guidebook-view";
import {
  REVISE_FIXTURE_AFTER,
  REVISE_FIXTURE_BEFORE,
} from "@/lib/revise-fixture";
import type { GuidebookExport } from "@/lib/sse";

/** Fixture chat+guidebook for Playwright revise proofs (no live generate). */
export default function ReviseFixturePage() {
  const [input, setInput] = useState("");
  const [guidebook, setGuidebook] = useState<GuidebookExport>(REVISE_FIXTURE_BEFORE);
  const [chatOnly, setChatOnly] = useState(0);
  const [status, setStatus] = useState("Draft ready — Revise plan uses composer text");
  const [reviseCalls, setReviseCalls] = useState(0);

  const onSend = (event: FormEvent) => {
    event.preventDefault();
    if (!input.trim()) return;
    setChatOnly((n) => n + 1);
    setStatus("Chat send only — draft unchanged");
    setInput("");
  };

  const onRevise = () => {
    const text = input.trim();
    if (!text) return;
    setReviseCalls((n) => n + 1);
    setStatus("Revising: packing");
    if (text.toLowerCase().includes("less walking")) {
      setGuidebook(REVISE_FIXTURE_AFTER);
      setStatus("Draft updated");
    }
    setInput("");
  };

  return (
    <main className="shell">
      <header className="no-print">
        <h1>Revise fixture</h1>
        <p className="status" data-testid="revise-fixture-status">
          {status}
        </p>
        <p data-testid="chat-only-count">chat-only:{chatOnly}</p>
        <p data-testid="revise-call-count">revise-calls:{reviseCalls}</p>
      </header>
      <div className="revise-panel no-print" role="group" aria-label="Revise plan">
        <button
          type="button"
          className="revise-plan"
          data-testid="revise-plan-btn"
          disabled={!input.trim()}
          onClick={onRevise}
        >
          Revise plan
        </button>
      </div>
      <GuidebookView
        exportData={guidebook}
        mapSlot={
          <div
            data-testid="trip-map"
            data-stop-ids={(guidebook.map_points ?? [])
              .map((p) => p.place_id)
              .join(",")}
          />
        }
      />
      <form onSubmit={onSend} className="no-print">
        <input
          data-testid="revise-composer"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="less walking day 2"
          aria-label="Message"
        />
        <button type="submit" data-testid="chat-send-btn" disabled={!input.trim()}>
          Send
        </button>
      </form>
    </main>
  );
}
