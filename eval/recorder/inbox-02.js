// inbox-02: archive and search mutate visible state; scheduled delivery is deliberately only promised.
const path = require("path");
const { record, moveTo, clickAt } = require("./common");

const APP = "file://" + path.join(__dirname, "inbox", "inbox.html");

record("inbox-02", {
  outDir: __dirname,
  setup: async (page) => {
    await page.goto(APP);
    await page.mouse.move(1100, 650);
    await page.waitForTimeout(1200);
  },
  script: async (page, at, mark) => {
    await at(3.5); await moveTo(page, page.getByRole("checkbox", { name: "Select Launch plan" }));
    await at(4.5); await clickAt(page, page.getByRole("checkbox", { name: "Select Launch plan" }));
    await at(5.2); await moveTo(page, page.getByRole("button", { name: "Archive selected" }));
    await at(6.0); await clickAt(page, page.getByRole("button", { name: "Archive selected" })); mark("message_archived");
    await at(11.0); await moveTo(page, page.getByRole("textbox", { name: "Search inbox" }));
    await at(12.0); await clickAt(page, page.getByRole("textbox", { name: "Search inbox" }));
    await page.keyboard.type("invoice", { delay: 170 }); mark("search_filtered");
    await at(19.0); await page.evaluate(() => window.showScheduled(true)); mark("scheduled_caption_on");
    await at(26.0); await page.evaluate(() => window.showScheduled(false)); mark("scheduled_caption_off");
    return 29.0;
  },
}).catch((error) => { console.error(error); process.exit(1); });
