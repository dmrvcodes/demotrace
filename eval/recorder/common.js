// Shared helpers for the scripted DemoTrace eval recordings.
// Each scenario records one continuous headless Chromium video, then mux.js adds Polly narration.
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PW_PATH);

// Headless video has no system cursor, so draw one plus a click ring.
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
    \`;
    document.head.appendChild(style);
    const cursor = document.createElement('div');
    cursor.id = 'fake-cursor';
    cursor.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 2l7 19 2.5-7.5L20 11z" fill="#111" stroke="#fff" stroke-width="1.5"/></svg>';
    document.body.appendChild(cursor);
    const last = JSON.parse(sessionStorage.getItem('fake-cursor') || '[640,360]');
    cursor.style.left = last[0] + 'px'; cursor.style.top = last[1] + 'px';
    document.addEventListener('mousemove', e => {
      cursor.style.left = e.clientX + 'px'; cursor.style.top = e.clientY + 'px';
      sessionStorage.setItem('fake-cursor', JSON.stringify([e.clientX, e.clientY]));
    }, true);
    document.addEventListener('mousedown', e => {
      const ring = document.createElement('div');
      ring.className = 'click-ring'; ring.style.left = e.clientX + 'px'; ring.style.top = e.clientY + 'px';
      document.body.appendChild(ring); setTimeout(() => ring.remove(), 600);
    }, true);
  });
`;

async function moveTo(page, locator, steps = 25) {
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps });
}

async function clickAt(page, locator, steps = 25) {
  await moveTo(page, locator, steps);
  await page.mouse.down();
  await page.mouse.up();
}

// Runs `setup(page)` (trimmed from the video), then `script(page, at, mark)` on a timeline
// measured from the end of setup. `mark(name)` records when something actually happened.
async function record(caseId, { setup, script, outDir }) {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: outDir, size: { width: 1280, height: 720 } },
  });
  await context.addInitScript(CURSOR_SCRIPT);
  const page = await context.newPage();
  const t0 = Date.now();
  await setup(page);
  const start = Date.now();
  const marks = {};
  const at = async (sec) => { const wait = start + sec * 1000 - Date.now(); if (wait > 0) await page.waitForTimeout(wait); };
  const mark = (name) => { marks[name] = Math.round((Date.now() - start) / 100) / 10; };
  const end = await script(page, at, mark);
  await at(end);
  const video = page.video();
  await context.close();
  const raw = path.join(outDir, `${caseId}.raw.webm`);
  fs.renameSync(await video.path(), raw);
  await browser.close();
  const timing = { case_id: caseId, trim_s: (start - t0) / 1000, duration_s: end, marks };
  fs.writeFileSync(path.join(outDir, `${caseId}.timing.json`), JSON.stringify(timing, null, 2));
  console.log(JSON.stringify(timing));
}

module.exports = { record, moveTo, clickAt };
