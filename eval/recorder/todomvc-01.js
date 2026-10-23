// Records the scripted TodoMVC demo for the DemoTrace eval case "todomvc-01".
// Writes raw.webm plus timing.json (how many seconds of setup to trim from the start).
const path = require("path");
const fs = require("fs");
const { chromium } = require(process.env.PW_PATH);

const OUT = __dirname;
const URL = "https://demo.playwright.dev/todomvc/#/";

// A visible cursor and click ring, because headless video has no system cursor.
const CURSOR_SCRIPT = `
  window.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = \`
      #fake-cursor { position: fixed; top: 0; left: 0; width: 22px; height: 22px; z-index: 2147483647;
        pointer-events: none; transform: translate(-3px, -2px); }
      .click-ring { position: fixed; width: 36px; height: 36px; margin: -18px 0 0 -18px; border-radius: 50%;
        border: 3px solid rgba(220, 60, 60, .85); pointer-events: none; z-index: 2147483646;
        animation: ring .5s ease-out forwards; }
      @keyframes ring { from { transform: scale(.4); opacity: 1 } to { transform: scale(1.3); opacity: 0 } }
      .todo-count, .filters li a, .clear-completed { font-size: 19px !important; }
    \`;
    document.head.appendChild(style);
    const cursor = document.createElement('div');
    cursor.id = 'fake-cursor';
    cursor.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 2l7 19 2.5-7.5L20 11z" fill="#111" stroke="#fff" stroke-width="1.5"/></svg>';
    document.body.appendChild(cursor);
    document.addEventListener('mousemove', e => { cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px'; }, true);
    document.addEventListener('mousedown', e => {
      const ring = document.createElement('div');
      ring.className = 'click-ring'; ring.style.left = e.clientX + 'px'; ring.style.top = e.clientY + 'px';
      document.body.appendChild(ring); setTimeout(() => ring.remove(), 600);
    }, true);
  });
`;

const SLIDE_ON = `(() => {
  const s = document.createElement('div');
  s.id = 'roadmap-slide';
  s.style.cssText = 'position:fixed;inset:0;background:#111;color:#fff;display:grid;place-items:center;' +
    'font:600 64px/1.25 -apple-system,Helvetica,Arial,sans-serif;text-align:center;z-index:2147483640';
  s.innerHTML = '<div>Coming soon:<br>due-date reminders</div>';
  document.body.appendChild(s);
})()`;
const SLIDE_OFF = `document.getElementById('roadmap-slide')?.remove()`;

async function moveTo(page, locator, steps = 25) {
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps });
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: OUT, size: { width: 1280, height: 720 } },
  });
  await context.addInitScript(CURSOR_SCRIPT);
  const page = await context.newPage();
  const t0 = Date.now();

  // Setup (trimmed later): two tasks, the second one completed.
  await page.goto(URL);
  const input = page.getByPlaceholder("What needs to be done?");
  await input.fill("Buy milk"); await input.press("Enter");
  await input.fill("Book flights"); await input.press("Enter");
  await page.getByTestId("todo-item").filter({ hasText: "Book flights" }).getByRole("checkbox").check();
  await page.mouse.move(640, 600);
  await page.waitForTimeout(1500);

  const start = Date.now();
  const at = async (sec) => { const wait = start + sec * 1000 - Date.now(); if (wait > 0) await page.waitForTimeout(wait); };

  // 0:00 intro (L1). 0:05 point at Buy milk, then the counter (L2).
  await at(5.2); await moveTo(page, page.getByTestId("todo-item").filter({ hasText: "Buy milk" }).getByTestId("todo-title"));
  await at(8.0); await moveTo(page, page.getByTestId("todo-count"));

  // 0:12 add a task (L3), 0:16 Enter -> counter becomes "2 items left" (L4).
  await at(12.3); await moveTo(page, input); await page.mouse.down(); await page.mouse.up();
  await at(13.0); await input.pressSequentially("Prepare demo", { delay: 140 });
  await at(16.0); await input.press("Enter");
  await at(17.0); await moveTo(page, page.getByTestId("todo-count"));

  // 0:22 Active filter; 0:24 click -> "Book flights" disappears (L5).
  await at(22.0); await moveTo(page, page.getByRole("link", { name: "Active" }));
  await at(24.0); await page.mouse.down(); await page.mouse.up();

  // 0:32 hover "Clear completed" and do NOT click (L6 at 0:35).
  await at(32.0); await moveTo(page, page.getByRole("button", { name: "Clear completed" }), 35);

  // 0:42 roadmap line (L7); 0:43.5 slide appears, silent until 0:53.
  await at(43.5); await page.evaluate(SLIDE_ON);
  await at(53.0); await page.evaluate(SLIDE_OFF); await page.mouse.move(640, 560, { steps: 20 });

  // 0:53.5 closing line (L8), hold until 1:05.
  await at(65.5);

  const trim = (start - t0) / 1000;
  const video = page.video();
  await context.close();
  const raw = path.join(OUT, "raw.webm");
  fs.renameSync(await video.path(), raw);
  fs.writeFileSync(path.join(OUT, "timing.json"), JSON.stringify({ trim_s: trim }, null, 2));
  await browser.close();
  console.log(JSON.stringify({ raw, trim_s: trim }));
})().catch(err => { console.error(err); process.exit(1); });
