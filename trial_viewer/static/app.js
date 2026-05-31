const state = {
  datasets: [],
  paths: [],
  summary: {},
  root: "",
  scannedAt: "",
  search: "",
  filter: "all",
};

const els = {};
let activePreviewButton = null;

document.addEventListener("DOMContentLoaded", () => {
  els.status = document.querySelector("#status");
  els.datasets = document.querySelector("#datasets");
  els.nav = document.querySelector("#dataset-nav");
  els.search = document.querySelector("#search");
  els.filter = document.querySelector("#filter");
  els.refresh = document.querySelector("#refresh");
  els.lightbox = document.querySelector("#lightbox");
  els.lightboxImage = document.querySelector("#lightbox-image");
  els.lightboxCaption = document.querySelector("#lightbox-caption");

  els.search.addEventListener("input", () => {
    state.search = els.search.value.trim().toLowerCase();
    render();
  });

  els.filter.addEventListener("change", () => {
    state.filter = els.filter.value;
    render();
  });

  els.refresh.addEventListener("click", loadData);
  els.datasets.addEventListener("click", handleDatasetClick);
  els.nav.addEventListener("click", handleNavClick);
  els.lightbox.addEventListener("click", handleLightboxClick);

  document.addEventListener("keydown", (event) => {
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

  loadData();
});

async function loadData() {
  els.refresh.disabled = true;
  els.refresh.textContent = "Refreshing";
  try {
    const response = await fetch("/api/datasets", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Scan failed with HTTP ${response.status}`);
    }
    const data = await response.json();
    state.datasets = data.datasets;
    state.paths = data.paths;
    state.summary = data.summary;
    state.root = data.root;
    state.scannedAt = data.scannedAt;
    render();
  } catch (error) {
    els.datasets.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    els.refresh.disabled = false;
    els.refresh.textContent = "Refresh";
  }
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
  els.status.innerHTML = [
    chip("Datasets", `${visibleCount}/${summary.datasetCount ?? 0}`),
    chip("Existing complete", summary.existingComplete ?? 0, "ok"),
    chip("Existing problems", summary.existingWithProblems ?? 0, summary.existingWithProblems ? "bad" : "ok"),
    chip("Folder 2", summary.draftFolders ?? 0, "warn"),
    chip("Draft complete", summary.draftComplete ?? 0, "ok"),
    chip("Need endings", summary.draftNeedsEndings ?? 0, summary.draftNeedsEndings ? "warn" : "ok"),
    chip("Extra images", summary.extraImages ?? 0, summary.extraImages ? "warn" : "ok"),
    chip("Scanned", state.scannedAt ? state.scannedAt.replace("T", " ") : ""),
  ].join("");
}

function chip(label, value, tone = "") {
  return `<span class="chip ${tone}">${escapeHtml(label)} <strong>${escapeHtml(String(value))}</strong></span>`;
}

function renderNav(datasets) {
  els.nav.innerHTML = datasets
    .map((dataset) => {
      const tone = dataset.issueTags.includes("existing-missing")
        ? "bad"
        : dataset.issueTags.some((tag) => tag.startsWith("draft") || tag === "extra-images")
          ? "warn"
          : "ok";
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

function renderDataset(dataset) {
  const tags = tagChips(dataset).join("");
  return `
    <article class="dataset-card" id="dataset-${dataset.number}">
      <header class="dataset-header">
        <div>
          <h2 class="dataset-title">Dataset ${dataset.number}: ${escapeHtml(dataset.displayName)}</h2>
          <p class="folder-path">${escapeHtml(dataset.folderPath)}</p>
        </div>
        <div class="dataset-tags">${tags}</div>
      </header>
      <div class="variant-grid">
        ${renderVariant(dataset, "existing", "Existing")}
        ${renderVariant(dataset, "draft", "Draft / folder 2")}
      </div>
    </article>
  `;
}

function tagChips(dataset) {
  const chips = [];
  chips.push(dataset.existing.complete ? chip("Existing", "8/8", "ok") : chip("Existing", `${8 - dataset.existing.missing.length}/8`, "bad"));

  if (!dataset.draft.exists) {
    chips.push(chip("Folder 2", "missing", "warn"));
  } else if (dataset.draft.fileCount === 0) {
    chips.push(chip("Folder 2", "empty", "warn"));
  } else if (dataset.draft.complete) {
    chips.push(chip("Draft", "8/8", "ok"));
  } else {
    chips.push(chip("Draft", `${8 - dataset.draft.missing.length}/8`, "warn"));
  }

  const extraCount = dataset.existing.extra.length + dataset.draft.extra.length;
  if (extraCount) {
    chips.push(chip("Extra", extraCount, "warn"));
  }
  return chips;
}

function renderVariant(dataset, key, title) {
  const variant = dataset[key];
  const status = variantStatus(variant, key);
  return `
    <section class="variant">
      <div class="variant-header">
        <h3>${escapeHtml(title)}</h3>
        ${status}
      </div>

      <p class="section-label">Core images</p>
      <div class="core-grid">
        ${["ic_1", "coh_1", "coh_2", "tr_target", "it_target"]
          .map((stem) => renderThumb(variant.images[stem], stem, dataset, key))
          .join("")}
      </div>

      <p class="section-label">Path previews</p>
      <div class="trial-list">
        ${state.paths.map((trial, index) => renderTrial(trial, index, variant, dataset, key)).join("")}
      </div>

      ${renderExtraImages(variant.extra, dataset, key)}
    </section>
  `;
}

function variantStatus(variant, key) {
  if (!variant.exists) {
    return chip(key === "draft" ? "Folder" : "Set", "missing", "warn");
  }
  if (variant.fileCount === 0) {
    return chip("Images", "0", "warn");
  }
  if (variant.complete) {
    return chip("Images", `${variant.fileCount}`, "ok");
  }
  return chip("Missing", variant.missing.length, "warn");
}

function renderTrial(trial, index, variant, dataset, key) {
  const steps = trial.steps
    .map((stem) => renderThumb(variant.images[stem], stem, dataset, key))
    .join('<span class="arrow" aria-hidden="true">&rarr;</span>');
  return `
    <section class="trial">
      <h4 class="trial-title"><span>${index + 1}.</span>${escapeHtml(trial.name)}</h4>
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

function renderThumb(image, stem, dataset, variant, extra = false) {
  if (!image) {
    return `
      <div class="thumb placeholder">
        <div class="placeholder-art">Missing</div>
        <div class="thumb-label"><span>${escapeHtml(stem)}</span></div>
      </div>
    `;
  }

  const caption = `Dataset ${dataset.number}: ${dataset.displayName} / ${variant} / ${image.filename}`;
  return `
    <button class="thumb" type="button" data-image="${escapeAttr(image.url)}" data-caption="${escapeAttr(caption)}">
      <img loading="lazy" src="${escapeAttr(image.url)}" alt="${escapeAttr(stem)}">
      <div class="thumb-label">
        <span>${escapeHtml(extra ? image.filename : stem)}</span>
      </div>
    </button>
  `;
}

function matchesFilters(dataset) {
  if (state.search) {
    const haystack = [
      dataset.number,
      dataset.displayName,
      dataset.folderName,
      dataset.folderPath,
    ].join(" ").toLowerCase();
    if (!haystack.includes(state.search)) {
      return false;
    }
  }

  switch (state.filter) {
    case "has-draft":
      return dataset.draft.exists;
    case "draft-incomplete":
      return dataset.draft.exists && !dataset.draft.complete;
    case "needs-endings":
      return dataset.issueTags.includes("draft-needs-endings");
    case "no-draft":
      return !dataset.draft.exists || dataset.draft.fileCount === 0;
    case "existing-problems":
      return !dataset.existing.complete;
    case "extras":
      return dataset.existing.extra.length + dataset.draft.extra.length > 0;
    default:
      return true;
  }
}

function handleDatasetClick(event) {
  const button = event.target.closest("[data-image]");
  if (!button) {
    return;
  }
  openLightbox(button);
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
