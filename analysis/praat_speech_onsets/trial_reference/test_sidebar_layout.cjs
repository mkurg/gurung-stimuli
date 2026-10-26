"use strict";
const {chromium} = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {spawn} = require("node:child_process");

// This fixture uses its own ephemeral server, TextGrid and decisions database.
async function fixture() {
  const python = process.env.PYTHON || "C:\\Users\\Sofya\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
  const child = spawn(python, [path.join(__dirname, "test_browser_server.py")],
    {cwd: __dirname, windowsHide: true, stdio: ["ignore", "pipe", "pipe"]});
  let output = "", errors = "";
  child.stderr.on("data", data => {errors += data;});
  try {
    const info = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Fixture startup timed out: " + errors)), 20000);
      child.on("error", error => {clearTimeout(timer); reject(error);});
      child.on("exit", () => {clearTimeout(timer); reject(new Error("Fixture exited: " + errors));});
      child.stdout.on("data", data => {
        output += data;
        if (output.includes("\n")) {clearTimeout(timer); resolve(JSON.parse(output.split("\n")[0]));}
      });
    });
    return {...info, child};
  } catch (error) {child.kill(); throw error;}
}

(async () => {
  const {url, child} = await fixture();
  let browser;
  try {
    browser = await chromium.launch({headless: true, channel: "msedge"});
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    const qa = path.join(__dirname, "qa", "sidebar-layout");
    fs.mkdirSync(qa, {recursive: true});
    const results = [];
    for (const viewport of [{width: 1440, height: 960}, {width: 1280, height: 632}, {width: 1024, height: 768}]) {
      await page.setViewportSize(viewport);
      await page.goto(url);
      await page.waitForFunction(() => document.querySelectorAll(".trial-row").length === 120);
      for (const phase of ["top", "middle", "bottom"]) {
        await page.evaluate(phase => window.scrollTo(0, phase === "top" ? 0 : phase === "middle" ? 160 : document.body.scrollHeight), phase);
        await page.waitForFunction(() => {
          const list = document.querySelector("#trial-list").getBoundingClientRect();
          const workspace = document.querySelector(".workspace").getBoundingClientRect();
          const sidebar = document.querySelector(".sidebar");
          const padding = parseFloat(getComputedStyle(sidebar).paddingBottom);
          return Math.abs(list.bottom + padding - Math.min(innerHeight, workspace.bottom)) < 2
            && Math.abs(sidebar.getBoundingClientRect().top - Math.max(0, workspace.top)) < 2;
        });
        const metrics = await page.evaluate(() => {
          const list = document.querySelector("#trial-list");
          return {height: list.clientHeight, scrollHeight: list.scrollHeight,
                  bottom: list.getBoundingClientRect().bottom, top: list.getBoundingClientRect().top,
                  sidebarTop: document.querySelector(".sidebar").getBoundingClientRect().top,
                  workspaceTop: document.querySelector(".workspace").getBoundingClientRect().top,
                  viewportHeight: innerHeight, horizontalOverflow: document.documentElement.scrollWidth > innerWidth};
        });
        assert.ok(metrics.height > 100, "Trial list must have usable height");
        assert.ok(metrics.scrollHeight > metrics.height, "Trial list must scroll independently");
        assert.ok(metrics.bottom <= viewport.height + 1, "Trial list must stay inside the viewport");
        assert.ok(!metrics.horizontalOverflow, "Layout must not overflow horizontally");
        assert.ok(Math.abs(metrics.sidebarTop - Math.max(0, metrics.workspaceTop)) < 2,
          "Sidebar controls follow the viewport while the page scrolls: " + JSON.stringify(metrics));
        await page.screenshot({path: path.join(qa, `${viewport.width}x${viewport.height}-${phase}.png`)});
        results.push({viewport, phase, ...metrics});
      }
      await page.locator("#trial-list").evaluate(list => {list.scrollTop = list.scrollHeight;});
      await page.locator('.trial-row[data-id="main-120"]').click();
      assert.equal(await page.locator("#trial-title").textContent(), "Trial 120");
    }
    await page.setViewportSize({width: 390, height: 844});
    await page.goto(url);
    await page.waitForFunction(() => document.querySelectorAll(".trial-row").length === 120);
    const mobile = await page.locator("#trial-list").evaluate(list => ({maxHeight: getComputedStyle(list).maxHeight, height: list.clientHeight}));
    assert.equal(mobile.maxHeight, "170px");
    assert.ok(mobile.height <= 170, "Mobile keeps its compact trial list");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({path: path.join(qa, "mobile.png"), fullPage: true});
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(qa, "metrics.json"), JSON.stringify({desktop: results, mobile}, null, 2));
    console.log(JSON.stringify({desktopCases: results.length, mobile, errors}, null, 2));
  } finally {
    if (browser) await browser.close();
    child.kill();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
