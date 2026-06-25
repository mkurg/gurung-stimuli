const DEFAULT_VISIBLE_SETS = ["1", "2", "3", "4"];
const GENERATION_STAT_SETS = ["3", "4"];
const FULL_SET_KEYS = ["1", "2", "3", "4"];
const CORE_IMAGE_STEMS = ["ic_1", "coh_1", "coh_2", "tr_target", "it_target"];
const MAX_DROP_FILE_BYTES = 24 * 1024 * 1024;
const MAX_REVIEW_TEXT_LENGTH = 3000;
const DEFAULT_REMOTE_REVIEW_API_BASE = "https://gurung.duckdns.org";
const REVIEW_STATUSES = new Set(["open", "on_review", "done", "deferred"]);
const REVIEW_STATUS_ALIASES = new Map([
  ["on review", "on_review"],
  ["on-review", "on_review"],
]);
const DEFAULT_EXPECTED_IMAGES = [
  ...CORE_IMAGE_STEMS,
  "end_coh_it",
  "end_ic_tr",
  "end_ic_it",
];

const state = {
  datasets: [],
  paths: [],
  summary: {},
  expected: [],
  setNumbers: ["1", "2", "3", "4"],
  visibleSets: [...DEFAULT_VISIBLE_SETS],
  root: "",
  scannedAt: "",
  search: "",
  filter: "all",
  currentDatasetNumber: "",
  currentDatasetName: "",
  reviews: {},
  reviewApiBase: "",
  reviewStatus: "",
  reviewsUpdatedAt: "",
  showImageSets: true,
  imageSetSize: 8,
  showPathPreviews: true,
  canSaveIdeas: false,
};

const els = {};
let activePreviewButton = null;
let activeIdeaTarget = null;
let activeDropTarget = null;
let activeReviewTarget = null;
let viewportUpdateFrame = 0;
let navJumpLockUntil = 0;

document.addEventListener("DOMContentLoaded", () => {
  els.topbar = document.querySelector(".topbar");
  els.status = document.querySelector("#status");
  els.datasets = document.querySelector("#datasets");
  els.nav = document.querySelector("#dataset-nav");
  els.search = document.querySelector("#search");
  els.filter = document.querySelector("#filter");
  els.setToggles = Array.from(document.querySelectorAll("[data-set-toggle]"));
  els.showImageSets = document.querySelector("#show-image-sets");
  els.imageSetSizeRadios = Array.from(document.querySelectorAll("[name='image-set-size']"));
  els.showPathPreviews = document.querySelector("#show-path-previews");
  els.refresh = document.querySelector("#refresh");
  els.lightbox = document.querySelector("#lightbox");
  els.lightboxImage = document.querySelector("#lightbox-image");
  els.lightboxCaption = document.querySelector("#lightbox-caption");
  els.ideaModal = document.querySelector("#idea-modal");
  els.ideaTitle = document.querySelector("#idea-title");
  els.ideaText = document.querySelector("#idea-text");
  els.ideaStatus = document.querySelector("#idea-status");
  els.ideaClose = document.querySelector("#idea-close");
  els.ideaCancel = document.querySelector("#idea-cancel");
  els.ideaClear = document.querySelector("#idea-clear");
  els.ideaSave = document.querySelector("#idea-save");
  els.reviewPanel = document.querySelector("#review-panel");
  els.reviewTitle = document.querySelector("#review-title");
  els.reviewList = document.querySelector("#review-list");
  els.reviewText = document.querySelector("#review-text");
  els.reviewStatus = document.querySelector("#review-status");
  els.reviewSave = document.querySelector("#review-save");

  els.search.addEventListener("input", () => {
    state.search = els.search.value.trim().toLowerCase();
    render();
  });

  els.filter.addEventListener("change", () => {
    state.filter = els.filter.value;
    render();
  });

  els.setToggles.forEach((input) => {
    input.addEventListener("change", () => {
      const selected = els.setToggles.filter((toggle) => toggle.checked).map((toggle) => toggle.value);
      if (!selected.length) {
        input.checked = true;
        return;
      }
      state.visibleSets = selected;
      render();
    });
  });

  els.showImageSets.addEventListener("change", () => {
    state.showImageSets = els.showImageSets.checked;
    syncViewControls();
    render();
    updateStickyOffset();
  });

  els.imageSetSizeRadios.forEach((input) => {
    input.addEventListener("change", () => {
      if (!input.checked) {
        return;
      }
      state.imageSetSize = Number(input.value);
      render();
    });
  });

  els.showPathPreviews.addEventListener("change", () => {
    state.showPathPreviews = els.showPathPreviews.checked;
    render();
    updateStickyOffset();
  });

  els.refresh.addEventListener("click", loadData);
  els.datasets.addEventListener("click", handleDatasetClick);
  els.datasets.addEventListener("dragover", handleDatasetDragOver);
  els.datasets.addEventListener("dragleave", handleDatasetDragLeave);
  els.datasets.addEventListener("drop", handleDatasetDrop);
  els.nav.addEventListener("click", handleNavClick);
  els.lightbox.addEventListener("click", handleLightboxClick);
  els.ideaModal.addEventListener("click", handleIdeaModalClick);
  els.ideaClose.addEventListener("click", closeIdeaModal);
  els.ideaCancel.addEventListener("click", closeIdeaModal);
  els.ideaClear.addEventListener("click", clearIdeaText);
  els.ideaSave.addEventListener("click", saveIdea);
  els.reviewSave.addEventListener("click", saveReview);
  els.reviewList.addEventListener("click", handleReviewListClick);
  window.addEventListener("resize", updateStickyOffset);
  window.addEventListener("scroll", scheduleViewportStateUpdate, { passive: true });
  if ("ResizeObserver" in window && els.topbar) {
    new ResizeObserver(updateStickyOffset).observe(els.topbar);
  }
  if ("ResizeObserver" in window && els.nav) {
    new ResizeObserver(updateStickyOffset).observe(els.nav);
  }

  document.addEventListener("keydown", (event) => {
    if (!els.ideaModal.hidden) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeIdeaModal();
      }
      return;
    }

    if (els.lightbox.hidden) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeLightbox();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      navigateLightboxByPlacement("right");
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      navigateLightboxByPlacement("left");
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      navigateLightboxByPlacement("down");
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      navigateLightboxByPlacement("up");
    }
  });

  updateStickyOffset();
  syncViewControls();
  loadData();
});

function updateStickyOffset() {
  const topbarHeight = els.topbar ? Math.ceil(els.topbar.getBoundingClientRect().height) : 0;
  const navHeight = els.nav ? Math.ceil(els.nav.getBoundingClientRect().height) : 0;
  document.documentElement.style.setProperty("--topbar-height", `${topbarHeight}px`);
  document.documentElement.style.setProperty("--nav-height", `${navHeight}px`);
  document.documentElement.style.setProperty("--sticky-offset", `${topbarHeight}px`);
  document.documentElement.style.setProperty("--dataset-scroll-margin", `${topbarHeight + navHeight + 28}px`);
}

async function loadData(options = {}) {
  els.refresh.disabled = true;
  els.refresh.textContent = "Refreshing";
  try {
    const { data, canSaveIdeas } = await fetchDatasetData();
    state.datasets = data.datasets;
    state.paths = data.paths;
    state.summary = data.summary;
    state.expected = data.expected ?? [];
    state.setNumbers = (data.setNumbers ?? ["1", "2", "3", "4"]).map(String);
    state.root = data.root;
    state.scannedAt = data.scannedAt;
    state.canSaveIdeas = canSaveIdeas;
    await loadReviews();
    syncSetToggles();
    render();
    restorePositionSnapshot(options.positionSnapshot);
  } catch (error) {
    els.datasets.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    els.refresh.disabled = false;
    els.refresh.textContent = "Refresh";
  }
}

async function fetchDatasetData() {
  try {
    return await fetchDatasetSource("/api/datasets");
  } catch (apiError) {
    if (!canFallBackToStaticData(apiError)) {
      throw new Error(`Could not load local PNG dataset data. ${apiError.message ?? ""}`.trim());
    }

    try {
      return await fetchDatasetSource("data/datasets.json");
    } catch (staticError) {
      throw new Error(`Could not load dataset data. ${staticError.message ?? apiError.message ?? ""}`.trim());
    }
  }
}

async function fetchDatasetSource(source) {
  const url = source === "/api/datasets" ? source : versionedDataUrl(source);
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    const error = new Error(`${source} returned HTTP ${response.status}`);
    error.source = source;
    error.status = response.status;
    throw error;
  }
  return {
    data: normalizeData(await response.json()),
    canSaveIdeas: source === "/api/datasets",
  };
}

function canFallBackToStaticData(error) {
  return error?.source === "/api/datasets" && [404, 405].includes(error.status);
}

function normalizeData(data) {
  const setNumbers = (data.setNumbers ?? [1, 2]).map(String);
  data.setNumbers = setNumbers;
  data.datasets = (data.datasets ?? []).map((dataset) => {
    if (!dataset.sets) {
      dataset.sets = {};
      if (dataset.existing) {
        dataset.sets["1"] = dataset.existing;
      }
      if (dataset.draft) {
        dataset.sets["2"] = dataset.draft;
      }
    }
    return dataset;
  });
  data.summary = data.summary ?? {};
  data.summary.sets = data.summary.sets ?? {};
  return data;
}

function syncSetToggles() {
  const available = availableSetKeys();
  state.visibleSets = state.visibleSets.filter((setKey) => available.includes(setKey));
  if (!state.visibleSets.length) {
    state.visibleSets = available.filter((setKey) => DEFAULT_VISIBLE_SETS.includes(setKey));
  }
  if (!state.visibleSets.length && available.length) {
    state.visibleSets = [available[0]];
  }

  els.setToggles.forEach((input) => {
    const availableSet = available.includes(input.value);
    input.disabled = !availableSet;
    input.checked = state.visibleSets.includes(input.value);
  });
}

function syncViewControls() {
  els.showImageSets.checked = state.showImageSets;
  els.imageSetSizeRadios.forEach((input) => {
    input.checked = Number(input.value) === state.imageSetSize;
    input.disabled = !state.showImageSets;
  });
  els.showPathPreviews.checked = state.showPathPreviews;
}

function versionedDataUrl(source) {
  const separator = source.includes("?") ? "&" : "?";
  return `${source}${separator}v=${Date.now()}`;
}

function isLocalHost() {
  return ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
}

function reviewApiBase() {
  const globalBase = typeof window.GURUNG_REVIEW_API_BASE === "string" ? window.GURUNG_REVIEW_API_BASE : "";
  const storedBase = safeLocalStorageGet("gurungReviewApiBase");
  const base = storedBase || globalBase || (isLocalHost() ? DEFAULT_REMOTE_REVIEW_API_BASE : "");
  return base.replace(/\/+$/, "");
}

function reviewApiUrl(path) {
  const base = state.reviewApiBase || reviewApiBase();
  return `${base}${path}`;
}

function safeLocalStorageGet(key) {
  try {
    return window.localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

async function loadReviews() {
  state.reviewApiBase = reviewApiBase();
  state.reviewStatus = "Loading reviews";
  try {
    const response = await fetchWithTimeout(versionedDataUrl(reviewApiUrl("/api/reviews")), {
      cache: "no-store",
    }, 3500);
    if (!response.ok) {
      throw new Error(`reviews returned HTTP ${response.status}`);
    }
    const payload = normalizeReviews(await response.json());
    state.reviews = payload.reviews;
    state.reviewsUpdatedAt = payload.updatedAt;
    state.reviewStatus = "ok";
  } catch (error) {
    state.reviews = {};
    state.reviewsUpdatedAt = "";
    state.reviewStatus = `Reviews unavailable: ${error.message}`;
  }
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

function normalizeReviews(payload) {
  const reviews = {};
  const rawReviews = payload?.reviews;
  if (rawReviews && typeof rawReviews === "object") {
    Object.entries(rawReviews).forEach(([key, entries]) => {
      if (!Array.isArray(entries)) {
        return;
      }
      const cleanEntries = entries
        .filter((entry) => entry && typeof entry.text === "string" && entry.text.trim())
        .map((entry) => {
          const status = normalizeReviewStatus(entry);
          return {
            id: typeof entry.id === "string" ? entry.id : "",
            text: entry.text.trim(),
            createdAt: typeof entry.createdAt === "string" ? entry.createdAt : "",
            status,
            done: status === "done",
            doneAt: typeof entry.doneAt === "string" ? entry.doneAt : "",
            deferredAt: typeof entry.deferredAt === "string" ? entry.deferredAt : "",
            onReviewAt: typeof entry.onReviewAt === "string" ? entry.onReviewAt : "",
          };
        });
      if (cleanEntries.length) {
        reviews[key] = cleanEntries;
      }
    });
  }
  return {
    reviews,
    updatedAt: typeof payload?.updatedAt === "string" ? payload.updatedAt : "",
  };
}

function normalizeReviewStatus(entry) {
  const status = normalizeReviewStatusValue(entry?.status);
  if (status) {
    return status;
  }
  return entry?.done === true ? "done" : "open";
}

function normalizeReviewStatusValue(status) {
  if (typeof status !== "string") {
    return "";
  }
  const cleanStatus = status.trim().toLowerCase();
  const canonicalStatus = REVIEW_STATUS_ALIASES.get(cleanStatus) ?? cleanStatus;
  return REVIEW_STATUSES.has(canonicalStatus) ? canonicalStatus : "";
}

function reviewStatusLabel(status) {
  if (status === "on_review") {
    return "On review";
  }
  if (status === "done") {
    return "Done";
  }
  if (status === "deferred") {
    return "Deferred";
  }
  return "Open";
}

function reviewKey(datasetNumber, setKey, stem) {
  return `${datasetNumber}:${setKey}:${stem}`;
}

function reviewsFor(datasetNumber, setKey, stem) {
  return state.reviews[reviewKey(datasetNumber, setKey, stem)] ?? [];
}

function reviewCountFor(datasetNumber, setKey, stem) {
  return reviewsFor(datasetNumber, setKey, stem).length;
}

function reviewSummaryFor(datasetNumber, setKey, stem) {
  const entries = reviewsFor(datasetNumber, setKey, stem);
  const latest = entries[entries.length - 1] ?? null;
  const latestStatus = latest?.status ?? "open";
  return {
    count: entries.length,
    latest,
    latestStatus,
    latestDone: latestStatus === "done",
  };
}

function allReviewCount() {
  return Object.values(state.reviews).reduce((total, entries) => total + entries.length, 0);
}

function availableSetKeys() {
  return (state.setNumbers.length ? state.setNumbers : ["1", "2", "3", "4"]).map(String);
}

function selectedSetKeys() {
  const available = availableSetKeys();
  const selected = state.visibleSets.filter((setKey) => available.includes(setKey));
  return selected.length ? selected : available.slice(0, 1);
}

function setData(dataset, setKey) {
  return dataset.sets?.[setKey] ?? {
    set: Number(setKey),
    exists: false,
    path: "",
    fileCount: 0,
    images: {},
    core: {},
    endings: {},
    missing: state.expected ?? [],
    extra: [],
    complete: false,
    ideas: {},
  };
}

function visibleSetData(dataset) {
  return selectedSetKeys().map((setKey) => [setKey, setData(dataset, setKey)]);
}

function render() {
  const visible = state.datasets.filter(matchesFilters);
  renderStatus(visible.length);
  renderNav(visible);

  if (!visible.length) {
    els.datasets.innerHTML = '<div class="empty-state">No datasets match the current view.</div>';
    scheduleViewportStateUpdate();
    return;
  }

  els.datasets.innerHTML = visible.map(renderDataset).join("");
  scheduleViewportStateUpdate();
}

function capturePositionSnapshot() {
  const gridScrollLeft = {};
  els.datasets.querySelectorAll(".dataset-card").forEach((card) => {
    const grid = card.querySelector(".set-grid");
    if (grid && card.dataset.datasetNumber) {
      gridScrollLeft[card.dataset.datasetNumber] = grid.scrollLeft;
    }
  });

  return {
    windowX: window.scrollX,
    windowY: window.scrollY,
    currentDatasetNumber: state.currentDatasetNumber,
    currentDatasetName: state.currentDatasetName,
    gridScrollLeft,
  };
}

function restorePositionSnapshot(snapshot) {
  if (!snapshot) {
    return;
  }

  const applySnapshot = () => {
    window.scrollTo(snapshot.windowX ?? 0, snapshot.windowY ?? 0);

    Object.entries(snapshot.gridScrollLeft ?? {}).forEach(([datasetNumber, scrollLeft]) => {
      const card = document.getElementById(`dataset-${datasetNumber}`);
      const grid = card?.querySelector(".set-grid");
      if (grid) {
        grid.scrollLeft = scrollLeft;
      }
    });

    if (snapshot.currentDatasetNumber) {
      setCurrentDataset(snapshot.currentDatasetNumber, snapshot.currentDatasetName);
    }
  };

  applySnapshot();
  requestAnimationFrame(applySnapshot);
}

function renderStatus(visibleCount) {
  const summary = state.summary;
  const generationSetKeys = selectedSetKeys().filter((setKey) => GENERATION_STAT_SETS.includes(setKey));
  const generationChips = generationSetKeys.map((setKey) =>
    pictureProgressChip(`Set ${setKey} images`, pictureProgressForSets([setKey])),
  );
  if (generationSetKeys.length) {
    generationChips.push(
      pictureProgressChip("Sets 3+4 images", pictureProgressForSets(GENERATION_STAT_SETS)),
    );
  }

  els.status.innerHTML = [
    chip("Datasets", `${visibleCount}/${summary.datasetCount ?? 0}`),
    reviewStatusChip(),
    ...generationChips,
    chip("Extra images", summary.extraImages ?? 0, summary.extraImages ? "warn" : "ok"),
    chip("Scanned", state.scannedAt ? state.scannedAt.replace("T", " ") : ""),
  ].join("");
}

function reviewStatusChip() {
  if (state.reviewStatus !== "ok") {
    return chip("Reviews", "offline", "warn");
  }
  return chip("Reviews", allReviewCount(), allReviewCount() ? "warn" : "ok");
}

function chip(label, value, tone = "") {
  return `<span class="chip ${tone}">${escapeHtml(label)} <strong>${escapeHtml(String(value))}</strong></span>`;
}

function pictureProgressChip(label, progress) {
  return chip(
    label,
    `${progress.present}/${progress.total} ${formatPercent(progress.percent)}`,
    progressToneCount(progress.present, progress.total),
  );
}

function pictureProgressForSets(setKeys) {
  const stems = expectedImageStems();
  const total = state.datasets.length * setKeys.length * stems.length;
  let present = 0;

  for (const dataset of state.datasets) {
    for (const setKey of setKeys) {
      const images = setData(dataset, setKey).images ?? {};
      for (const stem of stems) {
        if (images[stem]) {
          present += 1;
        }
      }
    }
  }

  return {
    present,
    total,
    percent: total ? (present / total) * 100 : 0,
  };
}

function expectedImageStems() {
  return state.expected.length ? state.expected : DEFAULT_EXPECTED_IMAGES;
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0%";
  }
  return `${Number.isInteger(number) ? number : number.toFixed(1)}%`;
}

function progressToneCount(value, total) {
  if (!total || value >= total) {
    return "ok";
  }
  return value ? "warn" : "bad";
}

function renderNav(datasets) {
  const current = currentDatasetFrom(datasets);
  state.currentDatasetNumber = current ? String(current.number) : "";
  state.currentDatasetName = current?.displayName ?? "";
  els.nav.innerHTML = `
    <div class="nav-current" aria-live="polite">
      <span>Current</span>
      <strong class="nav-current-number">${escapeHtml(state.currentDatasetNumber || "-")}</strong>
      <span class="nav-current-name">${escapeHtml(state.currentDatasetName)}</span>
    </div>
    <div class="nav-grid">
      ${datasets
        .map((dataset) => {
          const tone = datasetTone(dataset);
          const active = String(dataset.number) === state.currentDatasetNumber;
          return `
            <button
              class="nav-item ${active ? "active" : ""}"
              type="button"
              data-target="dataset-${dataset.number}"
              data-dataset-number="${dataset.number}"
              data-dataset-name="${escapeAttr(dataset.displayName)}"
              title="Dataset ${dataset.number}: ${escapeAttr(dataset.displayName)}"
              aria-label="Dataset ${dataset.number}: ${escapeAttr(dataset.displayName)}"
              ${active ? 'aria-current="true"' : ""}
            >
              <span class="nav-number">${dataset.number}</span>
              <span class="dot ${tone}" aria-hidden="true"></span>
            </button>
          `;
        })
        .join("")}
    </div>
  `;
}

function currentDatasetFrom(datasets) {
  if (!datasets.length) {
    return null;
  }
  return (
    datasets.find((dataset) => String(dataset.number) === state.currentDatasetNumber) ??
    datasets[0]
  );
}

function datasetTone(dataset) {
  const visibleSets = visibleSetData(dataset);
  if (visibleSets.some(([setKey, set]) => setKey === "1" && !set.complete)) {
    return "bad";
  }
  if (visibleSets.some(([, set]) => !set.exists || set.fileCount === 0 || !set.complete || set.extra.length)) {
    return "warn";
  }
  return "ok";
}

function renderDataset(dataset) {
  const tags = tagChips(dataset).join("");
  const setKeys = selectedSetKeys();
  return `
    <article
      class="dataset-card"
      id="dataset-${dataset.number}"
      data-dataset-number="${dataset.number}"
      data-dataset-name="${escapeAttr(dataset.displayName)}"
    >
      <header class="dataset-header">
        <div>
          <h2 class="dataset-title">Dataset ${dataset.number}: ${escapeHtml(dataset.displayName)}</h2>
          <p class="folder-path">${escapeHtml(dataset.folderPath)}</p>
        </div>
        <div class="dataset-tags">${tags}</div>
      </header>
      ${renderDatasetReviewList(dataset)}
      <div class="set-grid" style="--visible-set-count: ${setKeys.length}">
        ${setKeys.map((setKey) => renderSet(dataset, setKey)).join("")}
      </div>
    </article>
  `;
}

function renderDatasetReviewList(dataset) {
  const items = [];
  for (const [setKey, set] of visibleSetData(dataset)) {
    for (const [stem, image] of Object.entries(set.images ?? {})) {
      if (!image) {
        continue;
      }
      const entries = reviewsFor(dataset.number, setKey, stem);
      if (entries.length) {
        const latest = entries[entries.length - 1];
        items.push({
          setKey,
          stem,
          count: entries.length,
          latest: latest.text,
          latestStatus: latest.status ?? "open",
        });
      }
    }
  }

  if (!items.length) {
    return "";
  }

  return `
    <div class="dataset-review-list" aria-label="Picture reviews">
      ${items
        .map(
          (item) => `
            <button
              class="dataset-review-item is-${item.latestStatus}"
              type="button"
              data-review-target="true"
              data-dataset-number="${dataset.number}"
              data-dataset-name="${escapeAttr(dataset.displayName)}"
              data-set-number="${escapeAttr(item.setKey)}"
              data-stem="${escapeAttr(item.stem)}"
              title="${escapeAttr(`${reviewStatusLabel(item.latestStatus)}: set ${item.setKey} / ${item.stem}`)}"
              aria-label="${escapeAttr(`${reviewStatusLabel(item.latestStatus)} comment for set ${item.setKey} ${item.stem}`)}"
            >
              <strong>${escapeHtml(`Set ${item.setKey} / ${item.stem}`)}</strong>
              <span class="dataset-review-count">${item.count}</span>
              <em>${escapeHtml(item.latest)}</em>
            </button>
          `,
        )
        .join("")}
    </div>
  `;
}

function tagChips(dataset) {
  const chips = [];
  for (const [setKey, set] of visibleSetData(dataset)) {
    const tone = set.complete ? "ok" : setKey === "1" ? "bad" : "warn";
    const value = set.exists ? `${8 - set.missing.length}/8` : "missing";
    chips.push(chip(`Set ${setKey}`, value, tone));
  }

  const extraCount = visibleSetData(dataset).reduce((total, [, set]) => total + set.extra.length, 0);
  if (extraCount) {
    chips.push(chip("Extra", extraCount, "warn"));
  }
  return chips;
}

function renderSet(dataset, setKey) {
  const set = setData(dataset, setKey);
  const status = setStatus(set);
  const copyToneClass = ["2", "4"].includes(String(setKey)) ? " set-panel-copy" : "";
  return `
    <section class="set-panel${copyToneClass}" data-set-key="${escapeAttr(setKey)}">
      <div class="set-header">
        <h3>${escapeHtml(`Set ${setKey}`)}</h3>
        ${status}
      </div>

      ${state.showImageSets ? renderImageSet(set, dataset, setKey) : ""}
      ${state.showPathPreviews ? renderPathPreviews(set, dataset, setKey) : ""}

      ${renderExtraImages(set.extra, dataset, setKey)}
    </section>
  `;
}

function renderImageSet(set, dataset, setKey) {
  const stems = imageSetStems();
  const label = state.imageSetSize === 8 ? "Whole image set" : "Core images";
  return `
    <p class="section-label">${label}</p>
    <div class="core-grid">
      ${stems
        .map((stem) => renderThumb(set.images[stem], stem, dataset, setKey, false, set.ideas?.[stem]))
        .join("")}
    </div>
  `;
}

function imageSetStems() {
  return state.imageSetSize === 8 ? expectedImageStems() : CORE_IMAGE_STEMS;
}

function renderPathPreviews(set, dataset, setKey) {
  return `
    <p class="section-label">Path previews</p>
    <div class="trial-list">
      ${state.paths.map((trial, index) => renderTrial(trial, index, set, dataset, setKey)).join("")}
    </div>
  `;
}

function setStatus(set) {
  if (!set.exists) {
    return chip("Folder", "missing", "warn");
  }
  if (set.fileCount === 0) {
    return chip("Images", "0", "warn");
  }
  if (set.complete) {
    return chip("Images", `${set.fileCount}`, "ok");
  }
  return chip("Missing", set.missing.length, "warn");
}

function renderTrial(trial, index, set, dataset, setKey) {
  const steps = trial.steps
    .map((stem) => renderThumb(set.images[stem], stem, dataset, setKey, false, set.ideas?.[stem]))
    .join('<span class="arrow" aria-hidden="true">&rarr;</span>');
  return `
    <section class="trial">
      <h4 class="trial-title"><span>${dataset.number}.${index + 1}.</span>${escapeHtml(trial.name)}</h4>
      <div class="path-row">${steps}</div>
    </section>
  `;
}

function renderExtraImages(images, dataset, key) {
  if (!images.length) {
    return "";
  }
  return `
    <p class="section-label">Extra images</p>
    <div class="extra-list">
      ${images.map((image) => renderThumb(image, image.stem, dataset, key, true)).join("")}
    </div>
  `;
}

function renderThumb(image, stem, dataset, setKey, extra = false, idea = null) {
  if (!image) {
    const ideaText = idea?.text ?? "";
    return `
      <button
        class="thumb placeholder missing-thumb ${ideaText ? "has-idea" : ""}"
        type="button"
        data-missing="true"
        data-upload-target="true"
        data-has-image="false"
        data-dataset-number="${dataset.number}"
        data-dataset-name="${escapeAttr(dataset.displayName)}"
        data-set-number="${escapeAttr(setKey)}"
        data-stem="${escapeAttr(stem)}"
        data-idea="${escapeAttr(ideaText)}"
      >
        <div class="placeholder-art">
          <strong>Missing</strong>
          ${ideaText ? `<span>${escapeHtml(ideaText)}</span>` : "<em>Add idea</em>"}
        </div>
        <div class="thumb-label"><span>${escapeHtml(stem)}</span></div>
      </button>
    `;
  }

  const url = versionedImageUrl(image);
  const caption = `Dataset ${dataset.number}: ${dataset.displayName} / set ${setKey} / ${image.filename}`;
  const reviewSummary = extra ? { count: 0, latestStatus: "open" } : reviewSummaryFor(dataset.number, setKey, stem);
  const reviewCount = reviewSummary.count;
  const reviewStateClass = reviewCount ? `reviews-${reviewSummary.latestStatus}` : "";
  const uploadAttrs = extra
    ? ""
    : `
      data-upload-target="true"
      data-has-image="true"
      data-dataset-number="${dataset.number}"
      data-dataset-name="${escapeAttr(dataset.displayName)}"
      data-set-number="${escapeAttr(setKey)}"
      data-stem="${escapeAttr(stem)}"
    `;
  const reviewAttrs = extra
    ? ""
    : `
      data-review-target="true"
    `;
  return `
    <button class="thumb ${extra ? "" : "upload-target"} ${reviewCount ? "has-reviews" : ""} ${reviewStateClass}" type="button" data-image="${escapeAttr(url)}" data-caption="${escapeAttr(caption)}"${uploadAttrs}${reviewAttrs}>
      <img loading="lazy" src="${escapeAttr(url)}" alt="${escapeAttr(stem)}">
      <div class="thumb-label">
        <span>${escapeHtml(extra ? image.filename : stem)}</span>
        ${reviewCount ? `<strong class="review-badge is-${reviewSummary.latestStatus}">${reviewCount}</strong>` : ""}
      </div>
    </button>
  `;
}

function versionedImageUrl(image) {
  const key = [image.modified, image.sourceBytes, image.bytes]
    .filter((value) => value !== undefined && value !== null && value !== "")
    .join("-");

  if (!key) {
    return image.url;
  }

  const separator = image.url.includes("?") ? "&" : "?";
  return `${image.url}${separator}v=${encodeURIComponent(key)}`;
}

function matchesFilters(dataset) {
  if (state.search) {
    const haystack = [
      dataset.number,
      dataset.displayName,
      dataset.folderName,
      dataset.folderPath,
      ...Object.values(dataset.sets ?? {}).map((set) => set.path),
    ].join(" ").toLowerCase();
    if (!haystack.includes(state.search)) {
      return false;
    }
  }

  switch (state.filter) {
    case "full-sets":
      return allSetsReady(dataset);
    case "set-incomplete":
      return visibleSetData(dataset).some(([, set]) => !set.complete);
    case "core-incomplete":
      return coreImagesIncomplete(dataset);
    case "needs-endings":
      return visibleSetData(dataset).some(([, set]) => set.exists && set.fileCount > 0 && missingEndings(set));
    case "empty-set":
      return visibleSetData(dataset).some(([, set]) => !set.exists || set.fileCount === 0);
    case "existing-problems":
      return !setData(dataset, "1").complete;
    case "extras":
      return visibleSetData(dataset).some(([, set]) => set.extra.length > 0);
    default:
      return true;
  }
}

function allSetsReady(dataset) {
  return FULL_SET_KEYS.every((setKey) => setData(dataset, setKey).complete);
}

function coreImagesIncomplete(dataset) {
  return CORE_IMAGE_STEMS.some(
    (stem) => visibleSetData(dataset).some(([, set]) => !set.images[stem]),
  );
}

function missingEndings(set) {
  return ["end_coh_it", "end_ic_tr", "end_ic_it"].some((stem) => !set.images[stem]);
}

function uploadTargetFromEvent(event) {
  const target = event.target.closest("[data-upload-target]");
  if (!target || !els.datasets.contains(target)) {
    return null;
  }
  return target;
}

function setActiveDropTarget(target) {
  if (activeDropTarget === target) {
    return;
  }
  clearActiveDropTarget();
  activeDropTarget = target;
  activeDropTarget.classList.add("drag-over");
}

function clearActiveDropTarget() {
  if (!activeDropTarget) {
    return;
  }
  activeDropTarget.classList.remove("drag-over");
  activeDropTarget = null;
}

function handleDatasetDragOver(event) {
  const target = uploadTargetFromEvent(event);
  if (!target) {
    return;
  }
  event.preventDefault();
  event.dataTransfer.dropEffect = state.canSaveIdeas ? "copy" : "none";
  if (!state.canSaveIdeas) {
    return;
  }
  setActiveDropTarget(target);
}

function handleDatasetDragLeave(event) {
  if (!event.relatedTarget || !els.datasets.contains(event.relatedTarget)) {
    clearActiveDropTarget();
  }
}

async function handleDatasetDrop(event) {
  const target = uploadTargetFromEvent(event);
  if (!target) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();
  clearActiveDropTarget();

  if (!state.canSaveIdeas) {
    window.alert("Image drops only work in the local viewer.");
    return;
  }

  let imagePayload = null;
  try {
    imagePayload = await droppedImagePayload(event.dataTransfer);
  } catch (error) {
    window.alert(error.message);
    return;
  }

  if (!imagePayload) {
    window.alert("Drop an image file, or drag an image URL from the source page.");
    return;
  }

  const targetLabel = `Dataset ${target.dataset.datasetNumber}: ${target.dataset.datasetName} / set ${target.dataset.setNumber} / ${target.dataset.stem}.png`;
  const replacing = target.dataset.hasImage === "true";
  if (replacing && !window.confirm(`Replace ${targetLabel}?`)) {
    return;
  }

  const positionSnapshot = capturePositionSnapshot();
  try {
    const result = await uploadDroppedImage(target, imagePayload, replacing);
    if (result) {
      await loadData({ positionSnapshot });
      warnIfStaticRefreshFailed(result);
    }
  } catch (error) {
    window.alert(error.message);
  }
}

function warnIfStaticRefreshFailed(result) {
  const refresh = result?.staticRefresh;
  if (!refresh || refresh.ok) {
    return;
  }

  const exportError = refresh.export?.error;
  const publishError = refresh.publish?.error;
  const details = [exportError, publishError].filter(Boolean).join("\n\n");
  window.alert(
    `Saved locally, but the static picture update did not finish.${details ? `\n\n${details}` : ""}`,
  );
}

async function droppedImagePayload(dataTransfer) {
  const file = Array.from(dataTransfer.files ?? []).find((item) => isImageFile(item));
  if (file) {
    if (file.size > MAX_DROP_FILE_BYTES) {
      throw new Error("Image is too large.");
    }
    return { fileData: await readFileAsDataUrl(file) };
  }

  const sourceUrl = extractDroppedUrl(dataTransfer);
  return sourceUrl ? { sourceUrl } : null;
}

function isImageFile(file) {
  return file && (file.type.startsWith("image/") || /\.(png|jpe?g|webp|gif)$/i.test(file.name));
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(reader.result));
    reader.addEventListener("error", () => reject(new Error("Could not read dropped image.")));
    reader.readAsDataURL(file);
  });
}

function extractDroppedUrl(dataTransfer) {
  const uriList = dataTransfer.getData("text/uri-list");
  const uri = firstHttpUrl(uriList);
  if (uri) {
    return cleanDroppedUrl(uri);
  }

  const html = dataTransfer.getData("text/html");
  if (html) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const element = doc.querySelector("img[src], a[href]");
    const htmlUrl =
      element?.currentSrc ??
      element?.src ??
      element?.href ??
      element?.getAttribute("src") ??
      element?.getAttribute("href");
    if (htmlUrl && /^https?:\/\//i.test(htmlUrl)) {
      return cleanDroppedUrl(htmlUrl);
    }
  }

  return cleanDroppedUrl(firstHttpUrl(dataTransfer.getData("text/plain")));
}

function firstHttpUrl(text) {
  if (!text) {
    return "";
  }
  const lineUrl = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => /^https?:\/\//i.test(line));
  if (lineUrl) {
    return lineUrl;
  }
  const match = text.match(/https?:\/\/\S+/i);
  return match ? match[0] : "";
}

function cleanDroppedUrl(url) {
  const textarea = document.createElement("textarea");
  textarea.innerHTML = url.trim();
  return textarea.value.replace(/["')\]>]+$/g, "").trim();
}

async function uploadDroppedImage(target, imagePayload, overwrite) {
  target.classList.add("is-uploading");
  target.setAttribute("aria-busy", "true");
  setUploadStatus(target, "Saving...");
  try {
    const payload = {
      datasetNumber: Number(target.dataset.datasetNumber),
      setNumber: target.dataset.setNumber,
      stem: target.dataset.stem,
      overwrite,
      publishStatic: false,
      ...imagePayload,
    };

    const response = await fetch("/api/upload-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.status === 409 && !overwrite) {
      const error = await response.json().catch(() => ({}));
      if (window.confirm(`${error.error ?? "This slot already has an image."}\n\nReplace it?`)) {
        return await uploadDroppedImage(target, imagePayload, true);
      }
      return null;
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error ?? `Upload failed with HTTP ${response.status}`);
    }

    const uploadResult = await response.json();
    setUploadStatus(target, "Updating...");
    const publishResult = await publishStaticSite();
    return {
      ...uploadResult,
      staticRefresh: publishResult.staticRefresh ?? publishResult,
    };
  } finally {
    target.classList.remove("is-uploading");
    target.removeAttribute("aria-busy");
    target.removeAttribute("data-upload-status");
  }
}

function setUploadStatus(target, text) {
  target.dataset.uploadStatus = text;
}

async function publishStaticSite() {
  try {
    const response = await fetch("/api/publish-static", { method: "POST" });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        ok: false,
        staticRefresh: {
          ok: false,
          publish: { ok: false, error: error.error ?? `Publish failed with HTTP ${response.status}` },
        },
      };
    }
    return response.json();
  } catch (error) {
    return {
      ok: false,
      staticRefresh: {
        ok: false,
        publish: { ok: false, error: error.message },
      },
    };
  }
}

function handleDatasetClick(event) {
  const missingButton = event.target.closest("[data-missing]");
  if (missingButton) {
    openIdeaModal(missingButton);
    return;
  }

  const reviewButton = event.target.closest("[data-review-target]");
  if (reviewButton && !reviewButton.dataset.image) {
    const thumb = findReviewThumb(reviewButton);
    openLightbox(thumb ?? reviewButton);
    return;
  }

  const button = event.target.closest("[data-image]");
  if (!button) {
    return;
  }
  openLightbox(button);
}

function openIdeaModal(button) {
  activeIdeaTarget = {
    button,
    datasetNumber: Number(button.dataset.datasetNumber),
    datasetName: button.dataset.datasetName,
    setNumber: button.dataset.setNumber,
    stem: button.dataset.stem,
  };

  els.ideaTitle.textContent = `Dataset ${activeIdeaTarget.datasetNumber}: ${activeIdeaTarget.datasetName} / set ${activeIdeaTarget.setNumber} / ${activeIdeaTarget.stem}`;
  els.ideaText.value = button.dataset.idea ?? "";
  els.ideaStatus.textContent = state.canSaveIdeas
    ? ""
    : "Static export: edit this idea in the local viewer, then export again.";
  els.ideaText.disabled = !state.canSaveIdeas;
  els.ideaSave.disabled = !state.canSaveIdeas;
  els.ideaClear.disabled = !state.canSaveIdeas;
  els.ideaModal.hidden = false;
  els.ideaText.focus();
}

function handleIdeaModalClick(event) {
  if (event.target === els.ideaModal || event.target.classList.contains("modal-backdrop")) {
    closeIdeaModal();
  }
}

function closeIdeaModal() {
  els.ideaModal.hidden = true;
  activeIdeaTarget = null;
}

function clearIdeaText() {
  els.ideaText.value = "";
  els.ideaText.focus();
}

async function saveIdea() {
  if (!activeIdeaTarget || !state.canSaveIdeas) {
    return;
  }

  els.ideaSave.disabled = true;
  els.ideaStatus.textContent = "Saving...";

  try {
    const response = await fetch("/api/ideas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        datasetNumber: activeIdeaTarget.datasetNumber,
        setNumber: activeIdeaTarget.setNumber,
        stem: activeIdeaTarget.stem,
        text: els.ideaText.value,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error ?? `Save failed with HTTP ${response.status}`);
    }

    closeIdeaModal();
    await loadData();
  } catch (error) {
    els.ideaSave.disabled = false;
    els.ideaStatus.textContent = error.message;
  }
}

function handleNavClick(event) {
  const button = event.target.closest("[data-target]");
  if (!button) {
    return;
  }
  const target = document.getElementById(button.dataset.target);
  if (target) {
    navJumpLockUntil = performance.now() + 450;
    setCurrentDataset(button.dataset.datasetNumber, button.dataset.datasetName);
    scrollToDataset(target);
    window.setTimeout(scheduleViewportStateUpdate, 480);
  }
}

function scheduleViewportStateUpdate() {
  if (viewportUpdateFrame) {
    cancelAnimationFrame(viewportUpdateFrame);
  }
  viewportUpdateFrame = requestAnimationFrame(() => {
    viewportUpdateFrame = 0;
    updateStickyOffset();
    updateCurrentDataset();
  });
}

function updateCurrentDataset() {
  if (performance.now() < navJumpLockUntil) {
    return;
  }

  const cards = Array.from(els.datasets.querySelectorAll(".dataset-card"));
  if (!cards.length) {
    setCurrentDataset("", "");
    return;
  }

  const readLine = datasetReadLine();
  const covering = cards.find((card) => {
    const rect = card.getBoundingClientRect();
    return rect.top <= readLine && rect.bottom > readLine;
  });
  const nearest =
    covering ??
    cards
      .map((card) => ({
        card,
        distance: Math.abs(card.getBoundingClientRect().top - readLine),
      }))
      .sort((a, b) => a.distance - b.distance)[0]?.card;

  if (nearest) {
    setCurrentDataset(nearest.dataset.datasetNumber, nearest.dataset.datasetName);
  }
}

function datasetReadLine() {
  const topbarHeight = els.topbar ? els.topbar.getBoundingClientRect().height : 0;
  const navHeight = els.nav ? els.nav.getBoundingClientRect().height : 0;
  return topbarHeight + navHeight + 18;
}

function scrollToDataset(target) {
  const top = window.scrollY + target.getBoundingClientRect().top - datasetReadLine();
  window.scrollTo(0, Math.max(0, top));
}

function setCurrentDataset(number, name) {
  const normalizedNumber = number ? String(number) : "";
  const normalizedName = name ?? "";
  state.currentDatasetNumber = normalizedNumber;
  state.currentDatasetName = normalizedName;

  const numberElement = els.nav.querySelector(".nav-current-number");
  const nameElement = els.nav.querySelector(".nav-current-name");
  if (numberElement) {
    numberElement.textContent = normalizedNumber || "-";
  }
  if (nameElement) {
    nameElement.textContent = normalizedName;
  }

  els.nav.querySelectorAll(".nav-item").forEach((button) => {
    const active = button.dataset.datasetNumber === normalizedNumber;
    button.classList.toggle("active", active);
    if (active) {
      button.setAttribute("aria-current", "true");
    } else {
      button.removeAttribute("aria-current");
    }
  });
}

function openLightbox(button) {
  activePreviewButton = button;
  activeReviewTarget = reviewTargetFromElement(button);
  els.lightbox.classList.toggle("review-only", !button.dataset.image);
  els.lightboxImage.src = button.dataset.image ?? "";
  els.lightboxImage.alt = button.dataset.caption ?? reviewTitle(activeReviewTarget);
  els.lightboxCaption.textContent = button.dataset.caption ?? reviewTitle(activeReviewTarget);
  renderReviewPanel();
  els.lightbox.hidden = false;
}

function handleLightboxClick(event) {
  if (event.target === els.lightbox || event.target.classList.contains("lightbox-backdrop")) {
    closeLightbox();
  }
}

function closeLightbox() {
  if (els.lightbox.hidden) {
    return;
  }
  els.lightbox.hidden = true;
  els.lightbox.classList.remove("review-only");
  els.lightboxImage.src = "";
  activeReviewTarget = null;
  els.reviewText.value = "";
}

function findReviewThumb(target) {
  const selector = [
    "[data-image]",
    `[data-dataset-number="${cssEscape(target.dataset.datasetNumber)}"]`,
    `[data-set-number="${cssEscape(target.dataset.setNumber)}"]`,
    `[data-stem="${cssEscape(target.dataset.stem)}"]`,
  ].join("");
  return els.datasets.querySelector(selector);
}

function cssEscape(value) {
  if (window.CSS?.escape) {
    return window.CSS.escape(value ?? "");
  }
  return String(value ?? "").replaceAll('"', '\\"');
}

function reviewTargetFromElement(element) {
  if (!element?.dataset?.reviewTarget) {
    return null;
  }
  return {
    datasetNumber: Number(element.dataset.datasetNumber),
    datasetName: element.dataset.datasetName ?? "",
    setNumber: String(element.dataset.setNumber ?? ""),
    stem: element.dataset.stem ?? "",
  };
}

function reviewTitle(target) {
  if (!target) {
    return "Picture reviews";
  }
  return `Dataset ${target.datasetNumber}: ${target.datasetName} / set ${target.setNumber} / ${target.stem}`;
}

function renderReviewStatusLabel(entry) {
  return `<strong class="review-status-label is-${entry.status}">${escapeHtml(reviewStatusLabel(entry.status))}</strong>`;
}

function renderReviewActions(entry) {
  if (!entry.id) {
    return "";
  }

  return `
    ${entry.status !== "on_review" ? reviewStatusButton(entry.id, "on_review", "On review") : ""}
    ${entry.status !== "done" ? reviewStatusButton(entry.id, "done", "Mark done") : ""}
    ${entry.status !== "deferred" ? reviewStatusButton(entry.id, "deferred", "Defer") : ""}
    ${entry.status !== "open" ? reviewStatusButton(entry.id, "open", "Reopen") : ""}
    <button
      class="review-delete"
      type="button"
      data-review-action="delete"
      data-review-id="${escapeAttr(entry.id)}"
    >Delete</button>
  `;
}

function reviewStatusButton(reviewId, status, label) {
  return `
    <button
      class="review-status-toggle is-${status}"
      type="button"
      data-review-action="set-status"
      data-review-id="${escapeAttr(reviewId)}"
      data-review-status="${escapeAttr(status)}"
    >${escapeHtml(label)}</button>
  `;
}

function renderReviewStatusTime(entry) {
  if (entry.status === "on_review" && entry.onReviewAt) {
    return `<time class="review-status-at is-on_review">On review ${escapeHtml(entry.onReviewAt.replace("T", " "))}</time>`;
  }
  if (entry.status === "done" && entry.doneAt) {
    return `<time class="review-status-at is-done">Done ${escapeHtml(entry.doneAt.replace("T", " "))}</time>`;
  }
  if (entry.status === "deferred" && entry.deferredAt) {
    return `<time class="review-status-at is-deferred">Deferred ${escapeHtml(entry.deferredAt.replace("T", " "))}</time>`;
  }
  return "";
}

function renderReviewPanel() {
  if (!activeReviewTarget) {
    els.reviewPanel.hidden = true;
    return;
  }

  els.reviewPanel.hidden = false;
  els.reviewTitle.textContent = reviewTitle(activeReviewTarget);
  const entries = reviewsFor(
    activeReviewTarget.datasetNumber,
    activeReviewTarget.setNumber,
    activeReviewTarget.stem,
  );

  els.reviewList.innerHTML = entries.length
    ? entries
        .map(
          (entry) => `
            <article class="review-entry is-${entry.status}">
              <div class="review-entry-head">
                <div class="review-entry-meta">
                  ${renderReviewStatusLabel(entry)}
                  ${entry.createdAt ? `<time>${escapeHtml(entry.createdAt.replace("T", " "))}</time>` : "<span>Comment</span>"}
                </div>
                <div class="review-actions">
                  ${renderReviewActions(entry)}
                </div>
              </div>
              <p>${escapeHtml(entry.text)}</p>
              ${renderReviewStatusTime(entry)}
            </article>
          `,
        )
        .join("")
    : '<p class="review-empty">No comments yet.</p>';

  els.reviewText.value = "";
  els.reviewText.maxLength = MAX_REVIEW_TEXT_LENGTH;
  els.reviewSave.disabled = state.reviewStatus !== "ok";
  els.reviewStatus.textContent =
    state.reviewStatus === "ok"
      ? ""
      : `${state.reviewStatus}. Check the review server or API base.`;
}

async function saveReview() {
  if (!activeReviewTarget) {
    return;
  }

  const text = els.reviewText.value.trim();
  if (!text) {
    els.reviewStatus.textContent = "Write a comment first.";
    return;
  }

  els.reviewSave.disabled = true;
  els.reviewStatus.textContent = "Saving...";
  try {
    const response = await fetch(reviewApiUrl("/api/reviews"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        datasetNumber: activeReviewTarget.datasetNumber,
        setNumber: activeReviewTarget.setNumber,
        stem: activeReviewTarget.stem,
        text,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error ?? `Save failed with HTTP ${response.status}`);
    }

    const result = await response.json();
    const payload = normalizeReviews(result.reviews ?? result);
    state.reviews = payload.reviews;
    state.reviewsUpdatedAt = payload.updatedAt;
    state.reviewStatus = "ok";
    renderReviewPanel();
    render();
  } catch (error) {
    els.reviewSave.disabled = false;
    els.reviewStatus.textContent = error.message;
  }
}

function handleReviewListClick(event) {
  const button = event.target.closest("[data-review-action]");
  if (!button || !els.reviewList.contains(button)) {
    return;
  }
  if (button.dataset.reviewAction === "delete") {
    deleteReview(button.dataset.reviewId, button);
  } else if (button.dataset.reviewAction === "set-status") {
    setReviewStatus(button.dataset.reviewId, button.dataset.reviewStatus, button);
  }
}

async function deleteReview(reviewId, button) {
  if (!activeReviewTarget || !reviewId) {
    return;
  }
  if (!window.confirm("Delete this comment?")) {
    return;
  }

  button.disabled = true;
  els.reviewStatus.textContent = "Deleting...";
  try {
    const response = await fetch(reviewApiUrl("/api/reviews"), {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        datasetNumber: activeReviewTarget.datasetNumber,
        setNumber: activeReviewTarget.setNumber,
        stem: activeReviewTarget.stem,
        id: reviewId,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error ?? `Delete failed with HTTP ${response.status}`);
    }

    const result = await response.json();
    const payload = normalizeReviews(result.reviews ?? result);
    state.reviews = payload.reviews;
    state.reviewsUpdatedAt = payload.updatedAt;
    state.reviewStatus = "ok";
    renderReviewPanel();
    render();
  } catch (error) {
    button.disabled = false;
    els.reviewStatus.textContent = error.message;
  }
}

async function setReviewStatus(reviewId, status, button) {
  if (!activeReviewTarget || !reviewId) {
    return;
  }

  button.disabled = true;
  els.reviewStatus.textContent = reviewStatusProgressText(status);
  try {
    const response = await fetch(reviewApiUrl("/api/reviews"), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        datasetNumber: activeReviewTarget.datasetNumber,
        setNumber: activeReviewTarget.setNumber,
        stem: activeReviewTarget.stem,
        id: reviewId,
        status,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error ?? `Update failed with HTTP ${response.status}`);
    }

    const result = await response.json();
    const payload = normalizeReviews(result.reviews ?? result);
    state.reviews = payload.reviews;
    state.reviewsUpdatedAt = payload.updatedAt;
    state.reviewStatus = "ok";
    renderReviewPanel();
    render();
  } catch (error) {
    button.disabled = false;
    els.reviewStatus.textContent = error.message;
  }
}

function reviewStatusProgressText(status) {
  if (status === "on_review") {
    return "Marking on review...";
  }
  if (status === "done") {
    return "Marking done...";
  }
  if (status === "deferred") {
    return "Deferring...";
  }
  return "Reopening...";
}

function getPreviewItems() {
  return Array.from(els.datasets.querySelectorAll(".thumb[data-image]")).flatMap((button) => {
    const rect = button.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) {
      return [];
    }
    return [{ button, rect, center: centerOf(rect) }];
  });
}

function getActivePreviewItem(items) {
  const directMatch = items.find((item) => item.button === activePreviewButton);
  if (directMatch) {
    return directMatch;
  }

  const src = els.lightboxImage.getAttribute("src");
  const caption = els.lightboxCaption.textContent;
  return items.find(
    (item) => item.button.dataset.image === src && item.button.dataset.caption === caption,
  );
}

function navigateLightboxByPlacement(direction) {
  const items = getPreviewItems();
  if (!items.length) {
    return;
  }

  const current = getActivePreviewItem(items) ?? items[0];
  const next =
    direction === "left" || direction === "right"
      ? findHorizontalNeighbor(items, current, direction)
      : findVerticalNeighbor(items, current, direction);

  if (next) {
    openLightboxAt(next.button);
  }
}

function findHorizontalNeighbor(items, current, direction) {
  const sign = direction === "right" ? 1 : -1;

  return items
    .filter((item) => item.button !== current.button)
    .map((item) => ({
      ...item,
      primaryDistance: sign * (item.center.x - current.center.x),
      secondaryDistance: Math.abs(item.center.y - current.center.y),
      overlap: verticalOverlap(current.rect, item.rect),
    }))
    .filter((item) => item.primaryDistance > 8 && item.overlap > 0)
    .sort((a, b) => {
      const rowDifference = a.secondaryDistance - b.secondaryDistance;
      if (rowDifference !== 0) {
        return rowDifference;
      }
      return a.primaryDistance - b.primaryDistance;
    })[0];
}

function findVerticalNeighbor(items, current, direction) {
  const sign = direction === "down" ? 1 : -1;

  return items
    .filter((button) => button !== current)
    .map((item) => ({
      ...item,
      primaryDistance: sign * (item.center.y - current.center.y),
      secondaryDistance: Math.abs(item.center.x - current.center.x),
      overlap: horizontalOverlap(current.rect, item.rect),
    }))
    .filter((item) => item.primaryDistance > 8)
    .sort((a, b) => {
      const rowDifference = a.primaryDistance - b.primaryDistance;
      if (rowDifference !== 0) {
        return rowDifference;
      }
      const columnDifference = a.secondaryDistance - b.secondaryDistance;
      if (columnDifference !== 0) {
        return columnDifference;
      }
      return b.overlap - a.overlap;
    })[0];
}

function centerOf(rect) {
  return {
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2,
  };
}

function verticalOverlap(a, b) {
  return Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
}

function horizontalOverlap(a, b) {
  return Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
}

function openLightboxAt(button) {
  button.scrollIntoView({ block: "nearest", inline: "nearest" });
  openLightbox(button);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
