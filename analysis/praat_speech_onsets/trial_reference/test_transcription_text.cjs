"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function app() {
  const elements = new Map();
  const element = () => ({
    textContent: "", children: [], attributes: {},
    classList: {toggle() {}}, addEventListener() {},
    setAttribute(name, value) { this.attributes[name] = value; },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
  });
  const document = {
    addEventListener() {}, createElement: element,
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
    querySelector: () => element(),
  };
  const context = vm.createContext({
    document, window: {addEventListener() {}},
    location: {hash: "", href: "http://127.0.0.1:8765/"},
    fetch: () => new Promise(() => {}), AbortController,
    setTimeout: () => 0, clearTimeout() {},
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, "app.js"), "utf8"), context);
  return {run: code => vm.runInContext(code, context), elements};
}

test("trial sidebar fills the remaining viewport without covering the footer", () => {
  const {run} = app();
  assert.equal(run("trialSidebarHeight(960, 140, 1600)"), 820);
  assert.equal(run("trialSidebarHeight(960, 0, 1600)"), 960);
  assert.equal(run("trialSidebarHeight(960, -34, 926)"), 926);
  assert.equal(run("trialSidebarHeight(600, 700, 1600)"), 0);
});

test("renders all legacy tilde-e pairs as e with tilde above", () => {
  const {run} = app();
  assert.equal(run('transcriptionText("phr\\u02Dcesi \\u02Dce \\u02Dce")'), "phr\u1EBDsi \u1EBD \u1EBD");
  assert.equal(run('transcriptionText("e\\u0303 \\u1EBD")'), "\u1EBD \u1EBD");
  assert.equal(run('transcriptionText("ordinary e ~e e~ \\u02Dca \\u00F5")'), "ordinary e ~e e~ \u02Dca \u00F5");
});

test("updates assigned and unassigned display without changing saved text", () => {
  const {run, elements} = app();
  run(`state.selected = "main-001";
    state.annotations = {state: "ready", trials: {"main-001": {transcription: "phr\\u02Dcesi"}},
      unassigned_onsets: [], unassigned_transcriptions: [{start: 1, end: 2, text: "\\u02Dce <b>literal</b>"}]};
    updateAnnotations();`);
  assert.equal(elements.get("transcription-text").textContent, "phr\u1EBDsi");
  assert.equal(elements.get("annotation-issue-list").children[0].textContent,
    "Unassigned transcription: 1.0000 s - 2.0000 s: \u1EBD <b>literal</b>");
  assert.equal(run('state.annotations.trials["main-001"].transcription'), "phr\u02Dcesi");
  assert.equal(run('state.annotations.unassigned_transcriptions[0].text'), "\u02Dce <b>literal</b>");
});

test("search accepts legacy, composed, decomposed and uppercase tilde-e", () => {
  const {run} = app();
  run(`state.annotations = {trials: {"main-001": {transcription: "phr\\u02Dcesi"}}};
    var trial = {id: "main-001", number: 1, item: 12, start: 5, end: 10,
      scene: "scene", condition: "tr_coh", audio_filename: "trial.wav",
      triggers: [{code: 200, marker_id: "Mk7", label: "S200"}]};`);
  for (const query of ["phr\u02Dcesi", "phr\u1EBDsi", "phre\u0303si", "PHR\u1EBCSI", "PHR\u02DCESI"]) {
    assert.equal(run(`queryMatch(trial, ${JSON.stringify(query)})`), true);
  }
  for (const query of ["S200", "Mk7", "trial 1", "6.0 s"]) {
    assert.equal(run(`queryMatch(trial, ${JSON.stringify(query)})`), true);
  }
  assert.equal(run('queryMatch(trial, "phresi")'), false);
});

test("damaged practice WAV warning clears when switching to a main trial", () => {
  const {run, elements} = app();
  run(`configurePlayback = () => {};
    updateReviewControl = () => {};
    updateAnnotations = () => {};
    renderList = () => {};
    state.session = {recording: "131i", full_recording: {audio: "/media/full", filename: "full_session.wav"}};
    var warningTrial = {id: "practice-07", kind: "practice", number: 7, scene: "Practice", triggers: [],
      audio_filename: "damaged.wav", short_audio_warning: "Practice short WAV is unreadable."};
    selectTrial(warningTrial, false);`);
  assert.equal(elements.get("short-audio-warning").hidden, false);
  assert.equal(elements.get("short-audio-warning").textContent, "Practice short WAV is unreadable.");
  run('selectTrial({...warningTrial, id: "main-001", kind: "main", short_audio_warning: undefined}, false)');
  assert.equal(elements.get("short-audio-warning").hidden, true);
  assert.equal(elements.get("short-audio-warning").textContent, "");
});
