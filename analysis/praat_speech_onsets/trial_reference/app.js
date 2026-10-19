"use strict";
const $ = (id) => document.getElementById(id);
const state = {session: null, kind: "main", selected: null, query: "", filtered: [], marker: null, playback: null, reviews: {}, ergative: {}, needHelp: {}, saving: new Set(), saveErrors: {}, reviewFilter: "all", annotations: null, loading: false};
let sessionGeneration = 0;
let countsRequest = null;
function refreshCounts(force = false) {
  if (countsRequest && !force) return countsRequest.promise;
  countsRequest?.controller.abort();
  const request = {controller: new AbortController()};
  countsRequest = request;
  request.promise = (async () => {
    const timeout = setTimeout(() => request.controller.abort(), 30000);
    try {
      const response = await fetch("/api/library-counts", {cache: "no-store", signal: request.controller.signal});
      const snapshot = await response.json();
      if (!response.ok) throw new Error(snapshot.error || "Overall counts unavailable");
      if (countsRequest !== request) return;
      for (const [key, id] of [["itr", "count-itr"], ["tr_erg", "count-tr-erg"], ["tr_zero", "count-tr-zero"]]) {
        if (!Number.isInteger(snapshot.counts?.[key]) || snapshot.counts[key] < 0) throw new Error("Invalid overall counts");
        $(id).textContent = snapshot.counts[key].toLocaleString();
      }
      $("library-summary").title = `${snapshot.recordings} recordings / updated ${new Date(snapshot.updated_at_utc).toLocaleTimeString()}`;
      $("counts-status").hidden = true;
    } catch (error) {
      if (countsRequest !== request) return;
      for (const id of ["count-itr", "count-tr-erg", "count-tr-zero"]) $(id).textContent = "--";
      $("counts-status").textContent = "Unavailable"; $("counts-status").hidden = false;
      $("library-summary").title = error.name === "AbortError" ? "Overall counts timed out" : error.message;
    } finally {
      clearTimeout(timeout);
      if (countsRequest === request) countsRequest = null;
    }
  })();
  return request.promise;
}
const apiUrl = path => `${path}?session=${encodeURIComponent(state.session.session_id)}`;
const roles = {target_onset: "Picture onset", condition: "Condition", item: "Item", end: "Trial end", session: "Session event"};
const seconds = (value) => value == null ? "Not recorded" : `${value.toFixed(4)} s`;
const transcriptionText = text => text.replace(/\u02Dce/g, "\u1EBD").normalize("NFC");
const icons = () => window.lucide?.createIcons();
let toastTimer;
function toast(message) { $("toast").textContent = message; $("toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $("toast").hidden = true, 1800); }
async function copy(value) { try { await navigator.clipboard.writeText(value); toast("Copied"); } catch { toast("Clipboard unavailable"); } }
function updateExportControls() {
  $("export-suitability").setAttribute("aria-disabled", String(!state.session || state.loading || state.saving.size > 0));
  $("export-analysis").setAttribute("aria-disabled", String(state.loading || state.saving.size > 0 || state.annotations?.state !== "ready"));
  $("export-library").setAttribute("aria-disabled", String(state.loading || state.saving.size > 0));
  $("recording-select").disabled = state.loading || state.saving.size > 0;
  $("search").disabled = state.loading;
  $("trial-list").inert = state.loading || !state.session;
  document.querySelector(".tabs").inert = state.loading || !state.session;
  if (state.loading) { $("previous").disabled = true; $("next").disabled = true; }
  if (state.session) {
    $("export-suitability").href = apiUrl("/api/suitability.csv");
    $("export-analysis").href = apiUrl("/api/analysis.csv");
  }
}
function updateAnnotations() {
  const snapshot = state.annotations;
  const ready = snapshot?.state === "ready";
  const annotation = ready ? snapshot.trials[state.selected] : null;
  $("textgrid-name").textContent = snapshot?.filename || "No TextGrid configured";
  $("textgrid-name").title = snapshot?.path || "";
  $("annotation-sync").textContent = ready ? `Synced / saved ${new Date(snapshot.saved_at_utc).toLocaleTimeString()}` : snapshot?.message || "Loading saved TextGrid";
  $("annotation-sync").classList.toggle("sync-error", !!snapshot && !ready);
  $("annotation-s200").textContent = annotation?.s200_eeg_s == null ? "--" : seconds(annotation.s200_eeg_s);
  $("speech-onset").textContent = annotation?.speech_onset_eeg_s == null ? "--" : seconds(annotation.speech_onset_eeg_s);
  $("speech-latency").textContent = annotation?.latency_ms == null ? "--" : `${annotation.latency_ms.toFixed(1)} ms`;
  const warnings = [...(annotation?.warnings || [])];
  if (annotation?.status === "missing_onset") warnings.unshift("No saved speech-onset point.");
  if (annotation?.status === "no_eeg_triggers") warnings.unshift("No EEG trial triggers: no onset latency assigned.");
  if (annotation?.status === "multiple_onsets") warnings.push(annotation.onset_points.map(point => seconds(point.time)).join(", "));
  $("annotation-warning").hidden = !warnings.length;
  $("annotation-warning").textContent = warnings.join(" ");
  $("transcription-text").textContent = transcriptionText(annotation?.transcription || (ready ? "No saved transcription" : "Unavailable"));
  $("transcription-text").classList.toggle("no-transcription", !annotation?.transcription);
  const issues = ready ? [
    ...snapshot.unassigned_onsets.map(point => `Unassigned onset: ${seconds(point.time)} (${point.label || "unlabelled"})`),
    ...snapshot.unassigned_transcriptions.map(interval => `Unassigned transcription: ${seconds(interval.start)} - ${seconds(interval.end)}: ${transcriptionText(interval.text)}`),
  ] : [];
  $("annotation-issues").hidden = !issues.length;
  $("annotation-issue-count").textContent = `${issues.length} unassigned annotations in session`;
  $("annotation-issue-list").replaceChildren(...issues.map(text => {const p = document.createElement("p"); p.textContent = text; return p;}));
  updateExportControls();
}
let annotationPollTimer;
let annotationRequest = null;
function refreshAnnotations() {
  if (!state.session || state.loading) return Promise.resolve();
  if (annotationRequest?.sessionId === state.session.session_id) return annotationRequest.promise;
  annotationRequest?.controller.abort();
  clearTimeout(annotationPollTimer);
  const request = {sessionId: state.session.session_id, generation: sessionGeneration, controller: new AbortController()};
  annotationRequest = request;
  request.promise = (async () => {
    const controller = request.controller;
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(`/api/annotations?session=${encodeURIComponent(request.sessionId)}`, {signal: controller.signal, cache: "no-store"});
      if (!response.ok) throw new Error(`TextGrid request: ${response.status}`);
      const snapshot = await response.json();
      if (request.generation !== sessionGeneration) return;
      if (snapshot.session_id !== request.sessionId) throw new Error("Session changed. Refresh the page.");
      const signature = value => JSON.stringify([value?.state, value?.sha256, value?.saved_at_utc, value?.message, value?.path]);
      if (signature(snapshot) !== signature(state.annotations)) {
        state.annotations = snapshot; updateAnnotations();
        refreshCounts(true);
        if (state.query) renderList();
      }
    } catch (error) {
      if (request.generation !== sessionGeneration) return;
      state.annotations = {state: "error", filename: state.annotations?.filename, path: state.annotations?.path,
        message: error.name === "AbortError" ? "TextGrid sync timed out" : error.message};
      updateAnnotations();
    } finally {
      clearTimeout(timeout);
      if (annotationRequest === request) {
        annotationRequest = null;
        if (request.generation === sessionGeneration) annotationPollTimer = setTimeout(refreshAnnotations, 2000);
      }
    }
  })();
  return request.promise;
}
function updateReviewControl() {
  $("review-controls").hidden = !state.selected;
  updateExportControls();
  if (!state.selected) return;
  const decision = state.reviews[state.selected];
  const unsuitable = !!decision?.unsuitable;
  $("unsuitable").setAttribute("aria-pressed", String(unsuitable));
  $("unsuitable").disabled = state.saving.has(state.selected);
  $("unsuitable").title = unsuitable ? "Remove unsuitable flag" : "Mark behaviourally unsuitable";
  const trial = state.session.trials.find(trial => trial.id === state.selected);
  $("ergative").hidden = !trial.condition.startsWith("tr_") || !trial.triggers.some(t => t.role === "condition" && t.code === 1);
  for (const [id, values] of [["ergative", state.ergative], ["need-help", state.needHelp]]) {
    $(id).setAttribute("aria-pressed", String(!!values[state.selected]?.marked));
    $(id).disabled = state.saving.has(state.selected);
  }
  $("review-status").textContent = state.saving.has(state.selected) ? "Saving..." : state.saveErrors[state.selected] ? "Save failed" : decision || state.ergative[state.selected] || state.needHelp[state.selected] ? "Saved" : "";
  $("review-status").classList.toggle("save-error", !!state.saveErrors[state.selected]);
}
async function toggleFlag(field = "unsuitable") {
  const trialId = state.selected;
  if (!trialId || state.loading || state.saving.has(trialId)) return;
  const sessionId = state.session.session_id;
  const values = field === "unsuitable" ? state.reviews : field === "ergative" ? state.ergative : state.needHelp;
  const marked = field === "unsuitable" ? !values[trialId]?.unsuitable : !values[trialId]?.marked;
  state.saving.add(trialId); delete state.saveErrors[trialId]; updateReviewControl();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const endpoint = field === "unsuitable" ? "/api/suitability" : field === "ergative" ? "/api/ergative" : "/api/need-help";
    const response = await fetch(apiUrl(endpoint), {
      method: "POST", headers: {"Content-Type": "application/json"}, signal: controller.signal,
      body: JSON.stringify({session_id: sessionId, trial_id: trialId, [field]: marked}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Save failed");
    values[trialId] = result.decision;
    refreshCounts(true);
  } catch (error) {
    state.saveErrors[trialId] = error.message;
    toast(error.name === "AbortError" ? "Save timed out. Please retry." : error.message);
  } finally {
    clearTimeout(timeout); state.saving.delete(trialId); updateReviewControl(); renderList();
  }
}
let windowEndTimer;
function updatePlayButton() {
  const playing = !$("audio").paused;
  const label = playing ? "Pause" : "Play selected window";
  $("play-pause").setAttribute("aria-label", label); $("play-pause").title = label;
  $("play-pause").innerHTML = `<i data-lucide="${playing ? "pause" : "play"}"></i>`;
  icons();
}
function updateAudioPosition() {
  if (!state.playback) return;
  const time = Math.max(state.playback.start, Math.min(state.playback.end, $("audio").currentTime));
  $("seek").value = time; $("audio-position").value = `${time.toFixed(3)} s`;
}
function finishWindow() {
  clearTimeout(windowEndTimer);
  if (!state.playback || $("audio").paused) return;
  if ($("loop").checked) {
    $("audio").currentTime = state.playback.start;
    scheduleWindowEnd();
  } else {
    $("audio").pause(); $("audio").currentTime = state.playback.end;
  }
  updateAudioPosition();
}
function scheduleWindowEnd() {
  clearTimeout(windowEndTimer);
  if (!state.playback || $("audio").paused || $("audio").seeking) return;
  const remaining = (state.playback.end - $("audio").currentTime) / $("audio").playbackRate;
  windowEndTimer = setTimeout(finishWindow, Math.max(0, remaining * 1000));
}
function configurePlayback(trial) {
  const audio = $("audio"); audio.pause(); clearTimeout(windowEndTimer);
  state.playback = trial.playback; audio.loop = false;
  $("seek").min = state.playback.start; $("seek").max = state.playback.end; $("seek").value = state.playback.start;
  $("audio-position").value = `${state.playback.start.toFixed(3)} s`;
  $("window-start").textContent = `${state.playback.start.toFixed(3)} s`;
  $("window-end").textContent = `${state.playback.end.toFixed(3)} s`;
  $("audio-trial-start").textContent = `${state.playback.trial_start.toFixed(3)} s`;
  $("audio-trial-end").textContent = `${state.playback.trial_end.toFixed(3)} s`;
  if (audio.getAttribute("src") !== state.session.full_recording.audio) {
    audio.src = state.session.full_recording.audio; audio.load();
  } else if (audio.readyState >= 1) audio.currentTime = state.playback.start;
  audio.playbackRate = Number($("speed").value); updatePlayButton();
}
async function playWindow(restart = false) {
  if (!state.playback) return;
  const audio = $("audio");
  const selectedTrial = state.selected;
  const selectedSession = state.session.session_id;
  try {
    if (audio.readyState < 1) await new Promise((resolve, reject) => {
      audio.addEventListener("loadedmetadata", resolve, {once:true});
      audio.addEventListener("error", reject, {once:true});
    });
    if (!state.playback || state.selected !== selectedTrial || state.session?.session_id !== selectedSession) return;
    if (restart || audio.currentTime < state.playback.start || audio.currentTime >= state.playback.end - 0.02) audio.currentTime = state.playback.start;
    await audio.play(); scheduleWindowEnd();
  } catch { if (state.selected === selectedTrial && state.session?.session_id === selectedSession) toast("Audio playback unavailable"); }
}
function queryMatch(trial, query) {
  if (!query) return true;
  const q = transcriptionText(query.trim().toLowerCase());
  const code = q.match(/^s\s*(\d+)$/);
  if (code) return trial.triggers.some(t => t.code === Number(code[1]));
  const marker = q.match(/^mk\s*(\d+)$/);
  if (marker) return trial.triggers.some(t => t.marker_id.toLowerCase() === `mk${Number(marker[1])}`);
  const number = q.match(/^(?:trial|practice)\s*0*(\d+)$/);
  if (number) return trial.number === Number(number[1]);
  const time = q.match(/^(\d+\.\d+)\s*s?$/) || q.match(/^(\d+)\s*s$/);
  if (time) return trial.start != null && trial.start <= Number(time[1]) && trial.end >= Number(time[1]);
  if (/^\d+$/.test(q)) return trial.number === Number(q) || trial.item === Number(q);
  return transcriptionText([trial.audio_filename, trial.scene, trial.condition, trial.id, state.annotations?.trials?.[trial.id]?.transcription || "", ...trial.triggers.map(t => t.label)].join(" ").toLowerCase()).includes(q);
}
function eventMatch(t, query) {
  const q = query.trim().toLowerCase();
  if (!q) return !t.trial_id;
  const code = q.match(/^s\s*(\d+)$/);
  const mk = q.match(/^mk\s*(\d+)$/);
  if (code) return t.code === Number(code[1]);
  if (mk) return t.marker_id.toLowerCase() === `mk${Number(mk[1])}`;
  const time = q.match(/^(\d+(?:\.\d+)?)\s*s?$/);
  if (time) return Math.abs(t.time - Number(time[1])) <= 1;
  return `${t.label} ${t.marker_id} ${t.display}`.toLowerCase().includes(q);
}
function selectKind(kind) {
  state.kind = kind;
  for (const phase of ["main", "practice", "events"]) $(`${phase}-tab`).setAttribute("aria-selected", String(phase === kind));
  renderList();
}
function rowElement(entry, isEvent) {
  const button = document.createElement("button");
  button.className = "trial-row" + ((isEvent ? state.marker === entry.marker_id : state.selected === entry.id) ? " active" : "");
  button.dataset.id = isEvent ? entry.marker_id : entry.id;
  button.setAttribute("aria-pressed", String(button.classList.contains("active")));
  const title = document.createElement("span"); title.className = "row-title";
  title.textContent = isEvent ? entry.display : `${entry.kind === "main" ? "Trial" : "Practice"} ${String(entry.number).padStart(3,"0")}`;
  if (!isEvent && state.reviews[entry.id]?.unsuitable) {
    const mark = document.createElement("span"); mark.className = "unsuitable-mark"; mark.title = "Unsuitable";
    mark.setAttribute("role", "img"); mark.setAttribute("aria-label", "Unsuitable");
    mark.innerHTML = '<i data-lucide="ban" aria-hidden="true"></i>'; title.append(mark);
  }
  if (!isEvent) for (const [values, css, icon, label] of [[state.needHelp, "help-mark", "circle-help", "Need help"], [state.ergative, "ergative-mark", "tag", "Ergative"]]) {
    if (!values[entry.id]?.marked) continue;
    const mark = document.createElement("span"); mark.className = css; mark.title = label;
    mark.setAttribute("role", "img"); mark.setAttribute("aria-label", label);
    mark.innerHTML = `<i data-lucide="${icon}" aria-hidden="true"></i>`; title.append(mark);
  }
  const time = document.createElement("span"); time.className = "row-time"; time.textContent = isEvent ? entry.time.toFixed(4) : entry.start?.toFixed(4) ?? "--";
  const sub = document.createElement("span"); sub.className = "row-sub";
  sub.textContent = isEvent ? `${entry.marker_id} / ${entry.label}` : entry.kind === "main" ? `S ${entry.item} / image ${entry.image_set}, set ${entry.stimulus_set} / ${entry.condition}` : entry.scene;
  button.append(title, time, sub);
  button.addEventListener("click", () => isEvent ? selectEvent(entry) : selectTrial(entry));
  return button;
}
function renderList() {
  const isEvent = state.kind === "events";
  state.filtered = isEvent ? state.session.triggers.filter(t => eventMatch(t, state.query)) : state.session.trials.filter(t => t.kind === state.kind && queryMatch(t, state.query) && (state.reviewFilter === "all" || state.reviewFilter === "unsuitable" && state.reviews[t.id]?.unsuitable || state.reviewFilter === "need_help" && state.needHelp[t.id]?.marked || state.reviewFilter === "ergative" && state.ergative[t.id]?.marked));
  $("review-filter").disabled = isEvent;
  $("list-count").textContent = `${state.filtered.length} ${isEvent ? "events" : "trials"}`;
  $("trial-list").replaceChildren(...state.filtered.map(t => rowElement(t, isEvent)));
  if (!state.filtered.length) {
    const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "No matches."; $("trial-list").append(empty);
  }
  $("previous").disabled = isEvent || state.filtered.findIndex(t => t.id === state.selected) <= 0;
  $("next").disabled = isEvent || state.filtered.findIndex(t => t.id === state.selected) >= state.filtered.length - 1 || !state.filtered.length;
  icons();
}
function triggerTable(triggers) {
  const table = document.createElement("table");
  table.innerHTML = '<thead><tr><th>Role</th><th>Code</th><th class="numeric">EEG time (s)</th><th>Marker</th></tr></thead>';
  const body = document.createElement("tbody");
  for (const trigger of triggers) {
    const row = document.createElement("tr");
    if (trigger.role === "target_onset") row.classList.add("onset-row");
    const q = state.query.trim().toLowerCase();
    if (q.replace(/\s/g, "") === trigger.display.toLowerCase().replace(/\s/g,"" ) || q === trigger.marker_id.toLowerCase()) row.classList.add("highlight-row");
    for (const [value, style] of [[roles[trigger.role] || trigger.role,""], [trigger.display,"code"], [trigger.time.toFixed(4),"numeric"], [trigger.marker_id,"marker"]]) {
      const cell = document.createElement("td"); cell.className = style; cell.textContent = value;
      if (style === "numeric") { cell.title = `Copy ${trigger.time.toFixed(4)} seconds`; cell.style.cursor = "pointer"; cell.addEventListener("click", () => copy(trigger.time.toFixed(4))); }
      body.append(row); row.append(cell);
    }
  }
  table.append(body);
  return table;
}
function updateLocation(id) {
  const url = new URL(location.href); url.searchParams.set("session", state.session.session_id); url.hash = id;
  history.replaceState(null, "", url.pathname + url.search + url.hash);
  try { localStorage.setItem(`trial-reference-${state.session.session_id}`, id); } catch {}
}
function selectTrial(trial, update = true) {
  state.selected = trial.id; state.marker = null;
  $("audio-error").hidden = true; configurePlayback(trial);
  $("trial-content").hidden = false; $("event-content").hidden = true;
  $("phase").textContent = `${trial.kind.toUpperCase()} / ${state.session.recording}`;
  $("trial-title").textContent = `${trial.kind === "main" ? "Trial" : "Practice"} ${String(trial.number).padStart(3,"0")}`;
  $("picture").src = trial.image; $("picture").alt = trial.scene;
  $("scene").textContent = trial.scene;
  $("set-label").textContent = trial.kind === "main" ? `Image ${trial.image_set} / set ${trial.stimulus_set}` : "Practice";
  $("image-source").textContent = trial.image_source; $("image-path").textContent = trial.image_path;
  $("wav-name").textContent = trial.audio_filename; $("download-wav").href = state.session.full_recording.audio; $("download-wav").download = state.session.full_recording.filename;
  $("short-audio-warning").hidden = !trial.short_audio_warning;
  $("short-audio-warning").textContent = trial.short_audio_warning || "";
  $("trigger-count").textContent = trial.triggers.length ? `${trial.triggers.length} markers` : "No trial triggers";
  $("trigger-table").replaceChildren();
  if (trial.triggers.length) $("trigger-table").append(triggerTable(trial.triggers));
  else { const p = document.createElement("p"); p.className = "empty"; p.textContent = "Practice: no trial triggers were recorded."; $("trigger-table").append(p); }
  $("condition").textContent = trial.condition;
  $("image-set").textContent = trial.image_set == null ? "Practice" : `${trial.image_set} / set ${trial.stimulus_set}`;
  $("stimulus-onset").textContent = seconds(trial.start); $("trial-end").textContent = seconds(trial.end);
  $("praat-wav-path").textContent = state.session.praat_files?.wav || "";
  $("praat-grid-path").textContent = state.session.praat_files?.textgrid || "";
  $("selection-notice").hidden = trial.kind !== "practice";
  $("selection-notice").textContent = "Practice picture from the sequential experiment table. No EEG onset timestamp assigned.";
  updateReviewControl();
  updateAnnotations();
  if (update) updateLocation(trial.id);
  renderList();
}
function selectEvent(trigger) {
  state.marker = trigger.marker_id;
  if (trigger.trial_id) {
    const trial = state.session.trials.find(t => t.id === trigger.trial_id);
    state.kind = "main"; selectKind("main"); selectTrial(trial); return;
  }
  state.selected = null; $("audio").pause(); state.playback = null; clearTimeout(windowEndTimer);
  updateReviewControl();
  $("trial-content").hidden = true; $("event-content").hidden = false; $("selection-notice").hidden = true;
  $("phase").textContent = `SESSION EVENT / ${state.session.recording}`; $("trial-title").textContent = trigger.display;
  const heading = document.createElement("h3"); heading.className = "event-heading"; heading.textContent = trigger.label;
  const paragraph = document.createElement("p"); paragraph.textContent = "No trial picture or short WAV is associated with this session marker.";
  $("event-content").className = "event-summary"; $("event-content").replaceChildren(heading, triggerTable([trigger]), paragraph);
  renderList();
}
function search() {
  state.query = $("search").value;
  renderList();
  if (state.filtered.length) {
    state.kind === "events" ? selectEvent(state.filtered[0]) : selectTrial(state.filtered[0]);
  } else {
    $("selection-notice").hidden = false;
    $("selection-notice").textContent = "No matching trial in this phase. The displayed selection is unchanged.";
  }
}
for (const kind of ["main","practice","events"]) $(`${kind}-tab`).addEventListener("click", () => {
  selectKind(kind);
  if (state.filtered.length) kind === "events" ? selectEvent(state.filtered[0]) : selectTrial(state.filtered[0]);
});
$("search").addEventListener("input", search);
$("unsuitable").addEventListener("click", () => toggleFlag("unsuitable"));
$("ergative").addEventListener("click", () => toggleFlag("ergative"));
$("need-help").addEventListener("click", () => toggleFlag("need_help"));
$("review-filter").addEventListener("change", () => {
  state.reviewFilter = $("review-filter").value; renderList();
  if (state.filtered.length && !state.filtered.some(t => t.id === state.selected)) selectTrial(state.filtered[0]);
});
for (const id of ["export-suitability", "export-library"]) $(id).addEventListener("click", event => { if (state.saving.size || state.loading || !state.session) { event.preventDefault(); toast("Wait for the recording and decisions to finish loading."); } });
$("export-analysis").addEventListener("click", event => {
  if (state.saving.size || state.annotations?.state !== "ready") {
    event.preventDefault(); toast(state.saving.size ? "Decisions are still saving." : "A valid saved TextGrid is required.");
  }
});
$("refresh-annotations").addEventListener("click", refreshAnnotations);
document.addEventListener("visibilitychange", () => {if (!document.hidden) {refreshCounts(); if (state.session) refreshAnnotations();}});
window.addEventListener("focus", () => {refreshCounts(); if (state.session) refreshAnnotations();});
for (const [id, delta] of [["previous",-1],["next",1]]) $(id).addEventListener("click", () => {
  const index = state.filtered.findIndex(t => t.id === state.selected); const target = state.filtered[index + delta]; if (target) selectTrial(target);
});
$("copy-filename").addEventListener("click", () => copy($("wav-name").textContent));
$("play-pause").addEventListener("click", () => $("audio").paused ? playWindow() : $("audio").pause());
$("replay").addEventListener("click", () => playWindow(true));
$("seek").addEventListener("input", () => { $("audio").currentTime = Number($("seek").value); updateAudioPosition(); scheduleWindowEnd(); });
$("speed").addEventListener("change", () => $("audio").playbackRate = Number($("speed").value));
$("loop").addEventListener("change", scheduleWindowEnd);
$("volume").addEventListener("input", () => $("audio").volume = Number($("volume").value));
$("mute").addEventListener("click", () => {
  $("audio").muted = !$("audio").muted;
  const muted = $("audio").muted; const label = muted ? "Unmute" : "Mute";
  $("mute").setAttribute("aria-pressed", String(muted)); $("mute").setAttribute("aria-label", label); $("mute").title = label;
  $("mute").innerHTML = `<i data-lucide="${muted ? "volume-x" : "volume-2"}"></i>`; icons();
});
$("audio").addEventListener("loadedmetadata", () => { if (state.playback) $("audio").currentTime = state.playback.start; updateAudioPosition(); });
for (const event of ["play", "pause"]) $("audio").addEventListener(event, () => { updatePlayButton(); scheduleWindowEnd(); });
for (const event of ["seeked", "ratechange", "playing"]) $("audio").addEventListener(event, scheduleWindowEnd);
$("audio").addEventListener("waiting", () => clearTimeout(windowEndTimer));
$("audio").addEventListener("timeupdate", () => { updateAudioPosition(); if (state.playback && !$("audio").paused && $("audio").currentTime >= state.playback.end) finishWindow(); });
$("audio").addEventListener("error", () => { $("audio-error").hidden = false; $("audio-error").textContent = "This WAV could not be loaded."; });
$("zoom-picture").addEventListener("click", () => { $("large-picture").src = $("picture").src; $("dialog-title").textContent = `${$("trial-title").textContent} / ${$("scene").textContent}`; $("picture-dialog").showModal(); });
$("close-picture").addEventListener("click", () => $("picture-dialog").close());
$("picture-dialog").addEventListener("click", event => { if (event.target === $("picture-dialog")) $("picture-dialog").close(); });
async function loadSession(sessionId, desiredTrial = null) {
  if (state.saving.size) { $("recording-select").value = state.session.session_id; toast("Decisions are still saving."); return; }
  const generation = ++sessionGeneration;
  state.loading = true; clearTimeout(annotationPollTimer); annotationRequest?.controller.abort(); annotationRequest = null;
  $("audio").pause(); clearTimeout(windowEndTimer); state.playback = null;
  state.annotations = null; state.selected = null;
  $("trial-content").hidden = true; $("event-content").hidden = true; $("review-controls").hidden = true;
  $("trial-title").textContent = "Loading recording"; updateExportControls();
  try {
    const response = await fetch(sessionId ? `/api/session?session=${encodeURIComponent(sessionId)}` : "/api/session");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Session request: ${response.status}`);
    if (generation !== sessionGeneration) return;
    state.session = data;
    state.reviews = state.session.suitability || {};
    state.ergative = state.session.ergative || {}; state.needHelp = state.session.need_help || {};
    state.saveErrors = {}; state.query = ""; state.reviewFilter = "all"; $("search").value = ""; $("review-filter").value = "all";
    document.title = `${state.session.recording} | Trial Reference`;
    $("session-name").textContent = `${state.session.recording} / list ${state.session.list}`;
    $("recording-info").textContent = `${state.session.recording} / ${state.session.sample_rate.toLocaleString()} Hz`;
    $("main-count").textContent = state.session.validation.main_trials; $("practice-count").textContent = state.session.validation.practice_trials;
    $("validation-status").textContent = `${state.session.validation.matched_triggers} EEG triggers matched / ${state.session.validation.main_trials} main trials`;
    let saved; try { saved = localStorage.getItem(`trial-reference-${state.session.session_id}`) || localStorage.getItem(`trial-reference-${state.session.recording}`); } catch {}
    const desired = desiredTrial || saved;
    const trial = state.session.trials.find(t => t.id === desired) || state.session.trials[0];
    state.loading = false; $("recording-select").value = state.session.session_id;
    selectKind(trial.kind); selectTrial(trial); icons();
    await refreshAnnotations();
  } catch (error) {
    if (generation !== sessionGeneration) return;
    state.session = null; state.loading = false; updateExportControls();
    $("trial-title").textContent = "Session unavailable"; $("trial-content").hidden = true; $("selection-notice").hidden = false; $("selection-notice").textContent = error.message; $("validation-status").textContent = "Could not load session";
  }
}
let libraryTimer;
async function refreshLibrary() {
  clearTimeout(libraryTimer);
  refreshCounts();
  try {
    const response = await fetch("/api/sessions", {cache: "no-store"});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || "Library unavailable");
    const current = state.session?.session_id || $("recording-select").value;
    $("recording-select").replaceChildren(...data.sessions.map(session => {
      const option = document.createElement("option"); option.value = session.session_id;
      option.textContent = `${session.recording} / list ${session.list}${session.error ? " / unavailable" : ""}`; return option;
    }));
    if (data.sessions.some(session => session.session_id === current)) $("recording-select").value = current;
    $("library-status").textContent = `${data.sessions.length} recording${data.sessions.length === 1 ? "" : "s"}`;
    return data;
  } catch (error) { $("library-status").textContent = error.message; }
  finally { libraryTimer = setTimeout(refreshLibrary, 5000); }
}
$("recording-select").addEventListener("change", () => loadSession($("recording-select").value));
let importJob = null;
let importTimer;
async function pollImport() {
  if (!importJob) return;
  clearTimeout(importTimer);
  try {
    const response = await fetch(`/api/import/${encodeURIComponent(importJob.id)}`);
    const job = await response.json(); if (!response.ok) throw new Error(job.error || "Import unavailable");
    importJob = job;
    $("import-log").hidden = false; $("import-log").textContent = job.log.join("\n"); $("import-log").scrollTop = $("import-log").scrollHeight;
    $("import-state").textContent = job.state === "running" ? "Importing recording..." : job.state === "complete" ? "Updating recording library..." : job.error;
    $("import-submit").disabled = job.state === "running";
    if (job.state === "running") importTimer = setTimeout(pollImport, 1000);
    else {
      try { localStorage.removeItem("trial-reference-import"); } catch {}
      $("import-result").hidden = job.state !== "complete";
      if (job.state === "complete") { $("import-grid-result").textContent = job.result.textgrid; await refreshLibrary(); refreshCounts(true); $("import-state").textContent = "Recording ready"; }
    }
  } catch (error) { $("import-state").textContent = error.message; $("import-submit").disabled = false; }
}
$("add-recording").addEventListener("click", async () => {
  $("import-dialog").showModal();
  if (!$("import-experiment").value) {
    try {
      const defaults = await (await fetch("/api/import-defaults")).json();
      $("import-experiment").value = defaults.experiment_dir; $("import-channel").value = defaults.channel;
    } catch { $("import-state").textContent = "Import defaults unavailable"; }
  }
});
$("close-import").addEventListener("click", () => $("import-dialog").close());
$("import-form").addEventListener("submit", async event => {
  event.preventDefault(); $("import-submit").disabled = true; $("import-result").hidden = true; $("import-state").textContent = "Starting import...";
  try {
    const response = await fetch("/api/import", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(Object.fromEntries(new FormData($("import-form"))))});
    const job = await response.json(); if (!response.ok) throw new Error(job.error || "Could not start import");
    importJob = job; try { localStorage.setItem("trial-reference-import", job.id); } catch {}
    await pollImport();
  } catch (error) { $("import-state").textContent = error.message; $("import-submit").disabled = false; }
});
$("open-imported").addEventListener("click", () => {if (importJob?.result) {$("import-dialog").close(); loadSession(importJob.result.session_id);}});
async function initialize() {
  const desired = location.hash.slice(1);
  const library = await refreshLibrary();
  await loadSession(new URL(location.href).searchParams.get("session") || library?.default_session_id, desired);
  let pending; try { pending = localStorage.getItem("trial-reference-import"); } catch {}
  if (pending) { importJob = {id: pending}; await pollImport(); }
}
initialize();
