// silent-missing-01: no narration at all. A 0.7 s "Saved" toast between two 1-second samples,
// a persistent search filter, a caption-only promise, and one claim with no evidence anywhere.
const path = require("path");
const { record, moveTo, clickAt } = require("./common");

const APP = "file://" + path.join(__dirname, "notely", "notely.html");

record("silent-missing-01", {
  outDir: __dirname,
  setup: async (page) => {
    await page.goto(APP);
    await page.mouse.move(700, 600);
    await page.waitForTimeout(1200);
  },
  script: async (page, at, mark) => {
    await at(2.0); await moveTo(page, page.locator("li", { hasText: "Meeting notes" }));
    await at(3.0); await page.mouse.down(); await page.mouse.up(); mark("note_opened");
    await at(4.0); await clickAt(page, page.locator("#body"), 15);
    await page.keyboard.press("End");
    await page.keyboard.type(" Follow up on Friday.", { delay: 110 }); mark("typed");
    await at(7.8); await moveTo(page, page.getByRole("button", { name: "Save" }), 20);
    // Click between samples so the 0.7 s toast lives entirely inside (9 s, 10 s).
    await at(9.15); await page.mouse.down(); await page.mouse.up(); mark("save_clicked");
    await at(12.0); await moveTo(page, page.getByPlaceholder("Search notes"), 20);
    await at(13.0); await page.mouse.down(); await page.mouse.up();
    await at(14.0); await page.keyboard.type("meeting", { delay: 220 }); mark("search_typed");
    await at(17.0); await page.mouse.move(800, 420, { steps: 20 });
    await at(23.0); await page.evaluate(() => window.showCaption(true)); mark("caption_on");
    await at(30.0); await page.evaluate(() => window.showCaption(false)); mark("caption_off");
    return 33.0;
  },
}).catch((err) => { console.error(err); process.exit(1); });
