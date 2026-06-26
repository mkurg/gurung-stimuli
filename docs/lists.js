const SET_KEYS = ["1", "2", "3", "4"];

const DISCOURSE_CONDITIONS = {
  tr_coh: {
    label: "Transitive cohesive",
    countKey: "tr_coh",
    steps: ["coh_1", "coh_2", "tr_target"],
  },
  it_coh: {
    label: "Intransitive cohesive",
    countKey: "it_coh",
    steps: ["coh_1", "coh_2", "it_target", "end_coh_it"],
  },
  tr_ic: {
    label: "Transitive incohesive",
    countKey: "tr_ic",
    steps: ["ic_1", "tr_target", "end_ic_tr"],
  },
  it_ic: {
    label: "Intransitive incohesive",
    countKey: "it_ic",
    steps: ["ic_1", "it_target", "end_ic_it"],
  },
};

const ISOLATED_CONDITIONS = {
  tr: {
    label: "Transitive",
    countKey: "transitive",
    steps: ["tr_target"],
  },
  it: {
    label: "Intransitive",
    countKey: "intransitive",
    steps: ["it_target"],
  },
};

const EXPERIMENTS = {
  discourse: {
    label: "Discourse",
    eyebrow: "Picture sequences",
    expectedPerCondition: 60,
    conditions: DISCOURSE_CONDITIONS,
    countKeys: ["tr_coh", "tr_ic", "it_coh", "it_ic"],
    rules: {
      "1": {
        "1": ["it_coh", "tr_ic"],
        "2": ["tr_coh", "it_ic"],
        "3": ["tr_coh", "it_ic"],
        "4": ["it_coh", "tr_ic"],
      },
      "2": {
        "1": ["tr_coh", "it_ic"],
        "2": ["it_coh", "tr_ic"],
        "3": ["it_coh", "tr_ic"],
        "4": ["tr_coh", "it_ic"],
      },
    },
  },
  isolated: {
    label: "Isolated",
    eyebrow: "Target pictures",
    expectedPerCondition: 60,
    conditions: ISOLATED_CONDITIONS,
    countKeys: ["transitive", "intransitive"],
    rules: {
      "1": {
        "1": ["it"],
        "2": ["tr"],
        "3": ["tr"],
        "4": ["it"],
      },
      "2": {
        "1": ["tr"],
        "2": ["it"],
        "3": ["it"],
        "4": ["tr"],
      },
    },
  },
};

const state = {
  datasets: [],
  search: "",
  itemFilter: "all",
  experiment: "discourse",
};

const els = {};

document.addEventListener("DOMContentLoaded", () => {
  els.summary = document.querySelector("#summary");
  els.items = document.querySelector("#items");
  els.search = document.querySelector("#search");
  els.itemFilter = document.querySelector("#item-filter");
  els.experimentTabs = Array.from(document.querySelectorAll("[data-experiment]"));

  els.search.addEventListener("input", () => {
    state.search = els.search.value.trim().toLowerCase();
    render();
  });

  els.itemFilter.addEventListener("change", () => {
    state.itemFilter = els.itemFilter.value;
    render();
  });

  els.experimentTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.experiment = tab.dataset.experiment;
      render();
    });
  });

  loadData();
});

async function loadData() {
  try {
    const data = await fetchDatasetData();
    state.datasets = (data.datasets ?? []).map(normalizeDataset);
    populateItemFilter();
    render();
  } catch (error) {
    els.items.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function fetchDatasetData() {
  const sources = ["/api/datasets", "data/datasets.json"];
  let lastError = null;

  for (const source of sources) {
    try {
      const url = source === "/api/datasets" ? source : versionedUrl(source);
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${source} returned HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`Could not load experimental list data. ${lastError?.message ?? ""}`.trim());
}

function normalizeDataset(dataset) {
  return {
    ...dataset,
    number: Number(dataset.number),
    displayName: String(dataset.displayName ?? dataset.folderName ?? ""),
    sets: dataset.sets ?? {},
  };
}

function activeConfig() {
  return EXPERIMENTS[state.experiment] ?? EXPERIMENTS.discourse;
}

function populateItemFilter() {
  const options = ['<option value="all">All items</option>']
    .concat(
      state.datasets.map(
        (dataset) =>
          `<option value="${dataset.number}">${dataset.number}. ${escapeHtml(dataset.displayName)}</option>`,
      ),
    )
    .join("");
  els.itemFilter.innerHTML = options;
}

function render() {
  const filtered = filteredDatasets();
  els.experimentTabs.forEach((tab) => {
    const isActive = tab.dataset.experiment === state.experiment;
    tab.setAttribute("aria-selected", String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
  });
  els.summary.innerHTML = renderSummary(filtered);
  els.items.innerHTML = filtered.length
    ? renderListBoard(filtered)
    : '<div class="empty-state">No items match the current filter.</div>';
}

function filteredDatasets() {
  return state.datasets.filter((dataset) => {
    if (state.itemFilter !== "all" && String(dataset.number) !== state.itemFilter) {
      return false;
    }
    if (!state.search) {
      return true;
    }
    const haystack = `${dataset.number} ${dataset.displayName} ${dataset.folderName ?? ""}`.toLowerCase();
    return haystack.includes(state.search);
  });
}

function renderSummary(datasets) {
  const config = activeConfig();
  const allCounts = countLists(state.datasets, config);
  const visibleText =
    datasets.length === state.datasets.length
      ? `${state.datasets.length} items`
      : `${datasets.length} of ${state.datasets.length} items`;

  return `
    <div class="summary-main">
      <span class="chip"><strong>${escapeHtml(config.label)}</strong>${visibleText}</span>
      ${Object.entries(allCounts)
        .map(([listKey, counts]) => renderListSummaryChip(listKey, counts, config))
        .join("")}
    </div>
  `;
}

function renderListSummaryChip(listKey, counts, config) {
  const total = Object.values(counts.conditions).reduce((sum, value) => sum + value, 0);
  const ok = Object.values(counts.conditions).every((value) => value === config.expectedPerCondition);
  const title = Object.entries(counts.conditions)
    .map(([conditionId, value]) => `${conditionId}: ${value}`)
    .join(", ");
  return `
    <span class="chip ${ok ? "ok" : "bad"}" title="${escapeAttr(title)}">
      <strong>List ${listKey}</strong>
      ${total} trials
      ${Object.entries(counts.conditions)
        .map(
          ([conditionId, value]) =>
            `<em>${escapeHtml(conditionId)} ${value}/${config.expectedPerCondition}</em>`,
        )
        .join("")}
    </span>
  `;
}

function countLists(datasets, config = activeConfig()) {
  const counts = {
    "1": emptyCounts(config),
    "2": emptyCounts(config),
  };

  datasets.forEach((dataset) => {
    Object.entries(config.rules).forEach(([listKey, setRules]) => {
      SET_KEYS.forEach((setKey) => {
        (setRules[setKey] ?? []).forEach((conditionId) => {
          const condition = config.conditions[conditionId];
          counts[listKey].conditions[condition.countKey] += 1;
          condition.steps.forEach((stem) => {
            const image = dataset.sets?.[setKey]?.images?.[stem];
            if (!image) {
              counts[listKey].missingImages += 1;
            }
          });
        });
      });
    });
  });

  return counts;
}

function emptyCounts(config) {
  return {
    conditions: Object.fromEntries(config.countKeys.map((conditionId) => [conditionId, 0])),
    missingImages: 0,
  };
}

function renderListBoard(datasets) {
  const config = activeConfig();
  return `
    <div class="list-board ${state.experiment === "isolated" ? "isolated-board" : ""}">
      ${Object.keys(config.rules).map((listKey) => renderListColumn(datasets, listKey, config)).join("")}
    </div>
  `;
}

function renderListColumn(datasets, listKey, config) {
  const counts = countLists(datasets, config)[listKey];
  const total = Object.values(counts.conditions).reduce((sum, value) => sum + value, 0);
  const missing = counts.missingImages;
  return `
    <section class="list-column list-${listKey}" aria-label="${escapeAttr(config.label)} List ${listKey}">
      <header class="list-column-head">
        <div>
          <p class="eyebrow">${escapeHtml(config.eyebrow)}</p>
          <h2>List ${listKey}</h2>
        </div>
        <div class="list-column-counts">
          <span class="mini-chip ok">${total} trials</span>
          <span class="mini-chip ${missing ? "bad" : "ok"}">${missing ? `missing ${missing} images` : "all images present"}</span>
        </div>
      </header>
      <div class="list-trials">
        ${datasets.map((dataset) => renderListItemGroup(dataset, listKey, config)).join("")}
      </div>
    </section>
  `;
}

function renderListItemGroup(dataset, listKey, config) {
  const counts = countLists([dataset], config)[listKey];
  const missing = counts.missingImages;
  return `
    <article class="list-item-group" id="${state.experiment}-item-${dataset.number}-list-${listKey}">
      <header class="list-item-head">
        <div>
          <span>Item ${dataset.number}</span>
          <strong>${escapeHtml(dataset.displayName)}</strong>
        </div>
        <em class="${missing ? "bad" : "ok"}">${missing ? `missing ${missing}` : "complete"}</em>
      </header>
      <div class="set-groups">
        ${SET_KEYS.map((setKey) => renderSetGroup(dataset, listKey, setKey, config)).join("")}
      </div>
    </article>
  `;
}

function renderSetGroup(dataset, listKey, setKey, config) {
  const conditionIds = config.rules[listKey][setKey] ?? [];
  return `
    <section class="set-group">
      <div class="set-label">Set ${setKey}</div>
      <div class="trial-stack">
        ${conditionIds.map((conditionId) => renderTrial(dataset, setKey, conditionId, config)).join("")}
      </div>
    </section>
  `;
}

function renderTrial(dataset, setKey, conditionId, config) {
  const condition = config.conditions[conditionId];
  const images = condition.steps
    .map((stem, index) => renderTrialImage(dataset, setKey, stem, index < condition.steps.length - 1))
    .join("");
  const itemTrigger = (dataset.number - 1) * SET_KEYS.length + Number(setKey);
  return `
    <article class="trial-card">
      <header class="trial-head">
        <strong>${condition.label}</strong>
        <span>Item ${dataset.number} - Set ${setKey} - Trigger ${itemTrigger}</span>
      </header>
      <div class="sequence">${images}</div>
    </article>
  `;
}

function renderTrialImage(dataset, setKey, stem, showArrow) {
  const image = dataset.sets?.[setKey]?.images?.[stem];
  const body = image
    ? `<img src="${escapeAttr(versionedImageUrl(image.url, image.modified))}" alt="${escapeAttr(stem)}" loading="lazy">`
    : `<div class="missing-thumb"><strong>Missing</strong><span>${escapeHtml(stem)}</span></div>`;
  return `
    <figure class="seq-step">
      ${body}
      <figcaption>${escapeHtml(stem)}</figcaption>
    </figure>
    ${showArrow ? '<span class="arrow" aria-hidden="true">&rarr;</span>' : ""}
  `;
}

function versionedImageUrl(url, modified) {
  if (!url || !modified) {
    return url ?? "";
  }
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}v=${encodeURIComponent(modified)}`;
}

function versionedUrl(source) {
  const separator = source.includes("?") ? "&" : "?";
  return `${source}${separator}v=${Date.now()}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
