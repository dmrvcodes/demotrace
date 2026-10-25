// board-02: two unambiguous UI state changes, a coming-soon promise, and an absent feature.
const path = require("path");
const { record, moveTo, clickAt } = require("./common");

const APP = "file://" + path.join(__dirname, "board", "board.html");

record("board-02", {
  outDir: __dirname,
  setup: async (page) => {
    await page.goto(APP);
    await page.mouse.move(1120, 650);
    await page.waitForTimeout(1200);
  },
  script: async (page, at, mark) => {
    await at(4.0); await moveTo(page, page.getByRole("button", { name: "Move to In review" }));
    await at(5.5); await clickAt(page, page.getByRole("button", { name: "Move to In review" })); mark("landing_moved");
    await at(11.0); await moveTo(page, page.getByRole("button", { name: "+ New task" }));
    await at(12.5); await clickAt(page, page.getByRole("button", { name: "+ New task" })); mark("task_created");
    await at(18.5); await page.evaluate(() => window.showDigest(true)); mark("digest_caption_on");
    await at(25.0); await page.evaluate(() => window.showDigest(false)); mark("digest_caption_off");
    return 28.0;
  },
}).catch((error) => { console.error(error); process.exit(1); });
