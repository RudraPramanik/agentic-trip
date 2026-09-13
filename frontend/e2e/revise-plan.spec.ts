import { expect, test } from "@playwright/test";

test.describe("P6 revise plan smoke", () => {
  test("Revise plan visible after draft; send does not revise", async ({
    page,
  }) => {
    await page.goto("/revise-fixture");
    await expect(page.getByTestId("revise-plan-btn")).toBeVisible();
    await expect(page.getByTestId("guidebook-day-2")).toBeVisible();
    await expect(page.getByTestId("guidebook-stop-place-arashiyama")).toBeVisible();

    await page.getByTestId("revise-composer").fill("hello after draft");
    await page.getByTestId("chat-send-btn").click();
    await expect(page.getByTestId("chat-only-count")).toHaveText("chat-only:1");
    await expect(page.getByTestId("revise-call-count")).toHaveText("revise-calls:0");
    await expect(page.getByTestId("guidebook-stop-place-arashiyama")).toBeVisible();
  });

  test("successful revise updates guidebook and map stops", async ({ page }) => {
    await page.goto("/revise-fixture");
    await page.getByTestId("revise-composer").fill("less walking day 2");
    await page.getByTestId("revise-plan-btn").click();
    await expect(page.getByTestId("revise-call-count")).toHaveText("revise-calls:1");
    await expect(page.getByTestId("guidebook-stop-place-gion")).toBeVisible();
    await expect(page.getByTestId("guidebook-stop-place-kinkaku")).toBeVisible();
    await expect(page.getByTestId("guidebook-stop-place-arashiyama")).toHaveCount(0);
    await expect(page.getByTestId("guidebook-stop-place-bamboo")).toHaveCount(0);
    const map = page.getByTestId("trip-map");
    await expect(map).toHaveAttribute(
      "data-stop-ids",
      "place-fushimi,place-kiyomizu,place-gion,place-kinkaku",
    );
  });
});
