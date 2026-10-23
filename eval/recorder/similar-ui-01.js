// similar-ui-01: an interface that resembles a claim (hover reveals "View profile") without its
// result, plus an "as you can see" narration with nothing on screen. Site: the-internet.herokuapp.com.
const { record, moveTo, clickAt } = require("./common");
const BASE = "https://the-internet.herokuapp.com";

record("similar-ui-01", {
  outDir: __dirname,
  setup: async (page) => {
    await page.goto(`${BASE}/dynamic_loading/1`);
    await page.mouse.move(640, 500);
    await page.waitForTimeout(1200);
  },
  script: async (page, at, mark) => {
    // 0:04 "First, I'll reveal the hidden message." 0:06 click Start, ~5 s loading bar.
    await at(5.0); await moveTo(page, page.getByRole("button", { name: "Start" }));
    await at(6.0); await page.mouse.down(); await page.mouse.up(); mark("start_clicked");
    await page.locator("#finish").waitFor({ state: "visible" }); mark("hello_world_visible");
    await at(13.5); await page.mouse.move(640, 520, { steps: 15 });

    // 0:17 gallery; 0:18.5 narration; hover the first avatar, never click "View profile".
    await at(17.0); await page.goto(`${BASE}/hovers`); mark("hovers_loaded");
    await at(19.5); await moveTo(page, page.locator(".figure").first().locator("img"), 30); mark("hover_on");
    await page.locator(".figure").first().getByRole("link", { name: "View profile" }).waitFor({ state: "visible" });
    await at(27.0); mark("hover_end");

    // 0:28 add/remove; three clicks add three Delete buttons.
    await at(28.0); await page.goto(`${BASE}/add_remove_elements/`); mark("add_remove_loaded");
    const add = page.getByRole("button", { name: "Add Element" });
    await at(30.5); await clickAt(page, add); mark("add_1");
    await at(32.5); await page.mouse.down(); await page.mouse.up(); mark("add_2");
    await at(34.5); await page.mouse.down(); await page.mouse.up(); mark("add_3");
    await at(36.0); await page.mouse.move(640, 560, { steps: 15 });

    // 0:41 "As you can see, the app also saves your changes automatically." Nothing on screen.
    await at(41.0); mark("autosave_narration");
    return 54.0;
  },
}).catch((err) => { console.error(err); process.exit(1); });
