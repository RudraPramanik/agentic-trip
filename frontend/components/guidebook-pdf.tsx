"use client";

import {
  Document,
  Page,
  StyleSheet,
  Text,
  View,
  pdf,
} from "@react-pdf/renderer";

import type { GuidebookExport } from "@/lib/sse";
import {
  type GuidebookExportProjection,
  requireCompleteExport,
} from "@/lib/guidebook-export-view";

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontSize: 11,
    fontFamily: "Helvetica",
    color: "#1a1f1c",
  },
  title: { fontSize: 18, marginBottom: 6 },
  meta: { fontSize: 10, color: "#5c665f", marginBottom: 12 },
  dayTitle: { fontSize: 13, marginTop: 14, marginBottom: 4 },
  story: { marginBottom: 4, color: "#5c665f" },
  stop: { marginLeft: 8, marginBottom: 2 },
  booking: { marginTop: 20, paddingTop: 10, borderTopWidth: 1, borderTopColor: "#c5cdc7" },
});

function GuidebookPdfDocument({ projection }: { projection: GuidebookExportProjection }) {
  return (
    <Document title={projection.title}>
      <Page size="A4" style={styles.page}>
        <Text style={styles.title}>{projection.title}</Text>
        <Text style={styles.meta}>
          {projection.status} · {projection.day_count} days · {projection.stop_count}{" "}
          stops
        </Text>
        {projection.hubs.length > 0 ? (
          <Text style={styles.meta}>Hubs: {projection.hubs.join(" → ")}</Text>
        ) : null}
        {projection.days.map((day) => (
          <View key={day.day_index} wrap={false}>
            <Text style={styles.dayTitle}>
              Day {day.day_index}
              {day.title ? `: ${day.title}` : ""}
            </Text>
            {day.story ? <Text style={styles.story}>{day.story}</Text> : null}
            {day.stops.map((stop) => (
              <Text key={`${day.day_index}-${stop.place_id}`} style={styles.stop}>
                • {stop.label} ({stop.place_id})
              </Text>
            ))}
          </View>
        ))}
        <View style={styles.booking}>
          <Text style={styles.dayTitle}>Stays, flights & activities</Text>
          <Text style={styles.story}>
            Coming later — no rates or reservations yet.
          </Text>
        </View>
      </Page>
    </Document>
  );
}

/**
 * Render GuidebookExport → PDF blob. Pure DTO projection; never calls an LLM.
 */
export async function renderGuidebookPdf(
  exportData: GuidebookExport,
): Promise<Blob> {
  const check = requireCompleteExport(exportData);
  if (!check.ok) {
    throw new Error(check.error);
  }
  const instance = pdf(<GuidebookPdfDocument projection={check.projection} />);
  return instance.toBlob();
}

export async function downloadGuidebookPdf(
  exportData: GuidebookExport,
  filename?: string,
): Promise<void> {
  const blob = await renderGuidebookPdf(exportData);
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download =
      filename ??
      `${exportData.cover?.title?.replace(/[^\w\-]+/g, "_") || "guidebook"}.pdf`;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}

export { GuidebookPdfDocument };
