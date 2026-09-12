"use client";

import { useCallback, useState } from "react";

import { GuidebookPrintView } from "@/components/guidebook-print-view";
import { downloadGuidebookPdf } from "@/components/guidebook-pdf";
import type { GuidebookExport } from "@/lib/sse";
import { requireCompleteExport } from "@/lib/guidebook-export-view";

type Props = {
  exportData: GuidebookExport;
};

export function GuidebookExportActions({ exportData }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onPrint = useCallback(() => {
    setError(null);
    const check = requireCompleteExport(exportData);
    if (!check.ok) {
      setError(check.error);
      return;
    }
    window.print();
  }, [exportData]);

  const onDownload = useCallback(async () => {
    setError(null);
    const check = requireCompleteExport(exportData);
    if (!check.ok) {
      setError(check.error);
      return;
    }
    setBusy(true);
    try {
      await downloadGuidebookPdf(exportData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "PDF render failed — trip data was not changed.",
      );
    } finally {
      setBusy(false);
    }
  }, [exportData]);

  const check = requireCompleteExport(exportData);
  const projection = check.ok ? check.projection : null;

  return (
    <div className="guidebook-export-actions" data-testid="guidebook-export-actions">
      <div className="guidebook-export-buttons no-print" role="group" aria-label="Export guidebook">
        <button
          type="button"
          className="guidebook-print-btn"
          data-testid="guidebook-print-btn"
          onClick={onPrint}
          disabled={busy}
        >
          Print
        </button>
        <button
          type="button"
          className="guidebook-download-btn"
          data-testid="guidebook-download-btn"
          onClick={() => void onDownload()}
          disabled={busy}
        >
          {busy ? "Preparing PDF…" : "Download PDF"}
        </button>
      </div>
      {error ? (
        <p className="guidebook-export-error no-print" role="alert" data-testid="guidebook-export-error">
          {error}
        </p>
      ) : null}
      {projection ? <GuidebookPrintView projection={projection} /> : null}
    </div>
  );
}
