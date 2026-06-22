const DEFAULT_VISIBLE_SETS = ["1", "2"];
const GENERATION_STAT_SETS = ["3", "4"];
const FULL_SET_KEYS = ["1", "2", "3", "4"];
const CORE_IMAGE_STEMS = ["ic_1", "coh_1", "coh_2", "tr_target", "it_target"];
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
  showImageSets: true,
  imageSetSize: 5,
  showPathPreviews: true,
  canSaveIdeas: false,
};

const els = {};
let activePreviewButton = null;
let activeIdeaTarget = null;

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
  els.nav.addEventListener("click", handleNavClick);
  els.lightbox.addEventListener("click", handleLightboxClick);
  els.ideaModal.addEventListener("click", handleIdeaModalClick);
  els.ideaClose.addEventListener("click", closeIdeaModal);
  els.ideaCancel.addEventListener("click", closeIdeaModal);
  els.ideaClear.addEventListener("click", clearIdeaText);
  els.ideaSave.addEventListener("click", saveIdea);
  window.addEventListener("resize", updateStickyOffset);
  if ("ResizeObserver" in window && els.topbar) {
    new ResizeObserver(updateStickyOffset).observe(els.topbar);
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
  if (!els.topbar) {
    return;
  }
  const topbarHeight = Math.ceil(els.topbar.getBoundingClientRect().height);
  document.documentElement.style.setProperty("--sticky-offset", `${topbarHeight + 10}px`);
}

async function loadData() {
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
    syncSetToggles();
    render();
  } catch (error) {
    els.datasets.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    els.refresh.disabled = false;
    els.refresh.textContent = "Refresh";
  }
}

async function fetchDatasetData() {
  const sources = ["/api/datasets", "data/datasets.json"];
  let lastError = null;

  for (const source of sources) {
    try {
      const url = source === "/api/datasets" ? source : versionedDataUrl(source);
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${source} returned HTTP ${response.status}`);
      }
      return {
        data: normalizeData(await response.json()),
        canSaveIdeas: source === "/api/datasets",
      };
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`Could not load dataset data. ${lastError?.message ?? ""}`.trim());
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
    return;
  }

  els.datasets.innerHTML = visible.map(renderDataset).join("");
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
    ...generationChips,
    chip("Extra images", summary.extraImages ?? 0, summary.extraImages ? "warn" : "ok"),
    chip("Scanned", state.scannedAt ? state.scannedAt.replace("T", " ") : ""),
  ].join("");
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
  els.nav.innerHTML = datasets
    .map((dataset) => {
      const tone = datasetTone(dataset);
      return `
        <button class="nav-item" type="button" data-target="dataset-${dataset.number}">
          <span class="nav-number">${dataset.number}</span>
          <span class="nav-title">${escapeHtml(dataset.displayName)}</span>
          <span class="dot ${tone}" aria-hidden="true"></span>
        </button>
      `;
    })
    .join("");
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
    <article class="dataset-card" id="dataset-${dataset.number}">
      <header class="dataset-header">
        <div>
          <h2 class="dataset-title">Dataset ${dataset.number}: ${escapeHtml(dataset.displayName)}</h2>
          <p class="folder-path">${escapeHtml(dataset.folderPath)}</p>
        </div>
        <div class="dataset-tags">${tags}</div>
      </header>
      <div class="set-grid" style="--visible-set-count: ${setKeys.length}">
        ${setKeys.map((setKey) => renderSet(dataset, setKey)).join("")}
      </div>
    </article>
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
  return `
    <section class="set-panel">
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
  return `
    <button class="thumb" type="button" data-image="${escapeAttr(url)}" data-caption="${escapeAttr(caption)}">
      <img loading="lazy" src="${escapeAttr(url)}" alt="${escapeAttr(stem)}">
      <div class="thumb-label">
        <span>${escapeHtml(extra ? image.filename : stem)}</span>
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

function handleDatasetClick(event) {
  const missingButton = event.target.closest("[data-missing]");
  if (missingButton) {
    openIdeaModal(missingButton);
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
    target.scrollIntoView({ block: "start", behavior: "smooth" });
  }
}

function openLightbox(button) {
  activePreviewButton = button;
  els.lightboxImage.src = button.dataset.image;
  els.lightboxImage.alt = button.dataset.caption;
  els.lightboxCaption.textContent = button.dataset.caption;
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
  els.lightboxImage.src = "";
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
