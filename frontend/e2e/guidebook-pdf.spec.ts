import { expect, test } from "@playwright/test";

test.describe("P5b guidebook print/PDF smoke", () => {
  test("fixture page shows Print/Download and print DOM days", async ({
    page,
  }) => {
    await page.goto("/guidebook-fixture");
    await expect(page.getByTestId("guidebook-export-actions")).toBeVisible();
    await expect(page.getByTestId("guidebook-print-btn")).toBeVisible();
    await expect(page.getByTestId("guidebook-download-btn")).toBeVisible();

    // Print DOM is in the tree (hidden on screen via CSS; still queryable)
    const print = page.getByTestId("guidebook-print");
    await expect(print).toBeAttached();
    await expect(print.getByText("Day 1: Arrive")).toBeAttached();
    await expect(print.getByText("Old Bridge")).toBeAttached();
    await expect(print.getByText("Lighthouse")).toBeAttached();
    await expect(print.getByText("Coming later — no rates or reservations yet.")).toBeAttached();
  });

  test("Download PDF produces a PDF download", async ({ page }) => {
    await page.goto("/guidebook-fixture");
    const downloadPromise = page.waitForEvent("download");
    await page.getByTestId("guidebook-download-btn").click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.pdf$/i);
    const path = await download.path();
    expect(path).toBeTruthy();
  });
});
