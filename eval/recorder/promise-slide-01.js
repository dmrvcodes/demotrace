// promise-slide-01: a feature promised on a title slide, a screenshot of a button inside a slide,
// a real date-range change in the live app, and a two-part claim where only "create" is shown.
const path = require("path");
const { chromium } = require(process.env.PW_PATH);
const { record, moveTo } = require("./common");

const DIR = path.join(__dirname, "pulse");
const url = (file, query = "") => "file://" + path.join(DIR, file) + query;

(async () => {
  // The slide's screenshot of the dashboard, with the Export CSV button ringed (not recorded).
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(url("app.html", "?highlight=export"));
  await page.screenshot({ path: path.join(DIR, "pulse-shot.png") });
  await browser.close();

  await record("promise-slide-01", {
    outDir: __dirname,
    setup: async (page) => {
      await page.goto(url("slides.html", "?n=1"));
      await page.mouse.move(1180, 660);
      await page.waitForTimeout(1200);
    },
    script: async (page, at, mark) => {
      // 0:00 title slide promising AI anomaly alerts; 0:05.5 slide with the screenshot.
      await at(5.5); await page.goto(url("slides.html", "?n=2")); mark("slide_2");
      // 0:14 the live app.
      await at(14.0); await page.goto(url("app.html")); mark("app_loaded");
      await at(19.5); await moveTo(page, page.getByRole("button", { name: "30 days" }));
      await at(21.0); await page.mouse.down(); await page.mouse.up(); mark("range_30");
      await at(24.0); await page.mouse.move(700, 600, { steps: 20 });
      // 0:29 narration says "create ... and share"; only New dashboard is clicked.
      await at(30.0); await moveTo(page, page.getByRole("button", { name: "New dashboard" }));
      await at(31.5); await page.mouse.down(); await page.mouse.up(); mark("dashboard_created");
      await at(34.0); await page.mouse.move(820, 520, { steps: 20 });
      return 45.0;
    },
  });
})().catch((err) => { console.error(err); process.exit(1); });
