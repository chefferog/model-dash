/* ── Config ─────────────────────────────────────────────────────────────────── */

// Brand SVGs from Simple Icons (simpleicons.org) — MIT licensed
const ICONS = {
  anthropic: `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z"/></svg>`,
  openai:    `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M22.282 9.821a6 6 0 0 0-.516-4.91a6.05 6.05 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a6 6 0 0 0-3.998 2.9a6.05 6.05 0 0 0 .743 7.097a5.98 5.98 0 0 0 .51 4.911a6.05 6.05 0 0 0 6.515 2.9A6 6 0 0 0 13.26 24a6.06 6.06 0 0 0 5.772-4.206a6 6 0 0 0 3.997-2.9a6.06 6.06 0 0 0-.747-7.073M13.26 22.43a4.48 4.48 0 0 1-2.876-1.04l.141-.081l4.779-2.758a.8.8 0 0 0 .392-.681v-6.737l2.02 1.168a.07.07 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494M3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085l4.783 2.759a.77.77 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646M2.34 7.896a4.5 4.5 0 0 1 2.366-1.973V11.6a.77.77 0 0 0 .388.677l5.815 3.354l-2.02 1.168a.08.08 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.08.08 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667m2.01-3.023l-.141-.085l-4.774-2.782a.78.78 0 0 0-.785 0L9.409 9.23V6.897a.07.07 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.8.8 0 0 0-.393.681zm1.097-2.365l2.602-1.5l2.607 1.5v2.999l-2.597 1.5l-2.607-1.5Z"/></svg>`,
  google:    `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/></svg>`,
  meta:      `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6.915 4.03c-1.968 0-3.683 1.28-4.871 3.113C.704 9.208 0 11.883 0 14.449c0 .706.07 1.369.21 1.973a6.624 6.624 0 0 0 .265.86 5.297 5.297 0 0 0 .371.761c.696 1.159 1.818 1.927 3.593 1.927 1.497 0 2.633-.671 3.965-2.444.76-1.012 1.144-1.626 2.663-4.32l.756-1.339.186-.325c.061.1.121.196.183.3l2.152 3.595c.724 1.21 1.665 2.556 2.47 3.314 1.046.987 1.992 1.22 3.06 1.22 1.075 0 1.876-.355 2.455-.843a3.743 3.743 0 0 0 .81-.973c.542-.939.861-2.127.861-3.745 0-2.72-.681-5.357-2.084-7.45-1.282-1.912-2.957-2.93-4.716-2.93-1.047 0-2.088.467-3.053 1.308-.652.57-1.257 1.29-1.82 2.05-.69-.875-1.335-1.547-1.958-2.056-1.182-.966-2.315-1.303-3.454-1.303zm10.16 2.053c1.147 0 2.188.758 2.992 1.999 1.132 1.748 1.647 4.195 1.647 6.4 0 1.548-.368 2.9-1.839 2.9-.58 0-1.027-.23-1.664-1.004-.496-.601-1.343-1.878-2.832-4.358l-.617-1.028a44.908 44.908 0 0 0-1.255-1.98c.07-.109.141-.224.211-.327 1.12-1.667 2.118-2.602 3.358-2.602zm-10.201.553c1.265 0 2.058.791 2.675 1.446.307.327.737.871 1.234 1.579l-1.02 1.566c-.757 1.163-1.882 3.017-2.837 4.338-1.191 1.649-1.81 1.817-2.486 1.817-.524 0-1.038-.237-1.383-.794-.263-.426-.464-1.13-.464-2.046 0-2.221.63-4.535 1.66-6.088.454-.687.964-1.226 1.533-1.533a2.264 2.264 0 0 1 1.088-.285z"/></svg>`,
  nvidia:    `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M8.948 8.798v-1.43a6.7 6.7 0 0 1 .424-.018c3.922-.124 6.493 3.374 6.493 3.374s-2.774 3.851-5.75 3.851c-.398 0-.787-.062-1.158-.185v-4.346c1.528.185 1.837.857 2.747 2.385l2.04-1.714s-1.492-1.952-4-1.952a6.016 6.016 0 0 0-.796.035m0-4.735v2.138l.424-.027c5.45-.185 9.01 4.47 9.01 4.47s-4.08 4.964-8.33 4.964c-.37 0-.733-.035-1.095-.097v1.325c.3.035.61.062.91.062 3.957 0 6.82-2.023 9.593-4.408.459.371 2.34 1.263 2.73 1.652-2.633 2.208-8.772 3.984-12.253 3.984-.335 0-.653-.018-.971-.053v1.864H24V4.063zm0 10.326v1.131c-3.657-.654-4.673-4.46-4.673-4.46s1.758-1.944 4.673-2.262v1.237H8.94c-1.528-.186-2.73 1.245-2.73 1.245s.68 2.412 2.739 3.11M2.456 10.9s2.164-3.197 6.5-3.533V6.201C4.153 6.59 0 10.653 0 10.653s2.35 6.802 8.948 7.42v-1.237c-4.84-.6-6.492-5.936-6.492-5.936z"/></svg>`,
  mistral:   `<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M17.143 3.429v3.428h-3.429v3.429h-3.428V6.857H6.857V3.43H3.43v13.714H0v3.428h10.286v-3.428H6.857v-3.429h3.429v3.429h3.429v-3.429h3.428v3.429h-3.428v3.428H24v-3.428h-3.43V3.429z"/></svg>`,
};

const PROVIDER_META = {
  anthropic: { icon: ICONS.anthropic, label: "Anthropic" },
  openai:    { icon: ICONS.openai,    label: "OpenAI" },
  google:    { icon: ICONS.google,    label: "Google" },
  meta:      { icon: ICONS.meta,      label: "Meta" },
  nvidia:    { icon: ICONS.nvidia,    label: "NVIDIA" },
  mistral:   { icon: ICONS.mistral,   label: "Mistral" },
};

const PROVIDER_ORDER = ["anthropic", "openai", "google", "meta", "nvidia", "mistral"];

/* ── State ──────────────────────────────────────────────────────────────────── */
let autoRefreshTimer = null;

/* ── DOM refs ───────────────────────────────────────────────────────────────── */
const grid         = document.getElementById("modelGrid");
const refreshBtn   = document.getElementById("refreshBtn");
const refreshIcon  = document.getElementById("refreshIcon");
const lastUpdated  = document.getElementById("lastUpdated");
const statusDot    = document.getElementById("statusDot");
const pollSelect   = document.getElementById("pollInterval");

/* ── Boot ───────────────────────────────────────────────────────────────────── */
(async function init() {
  renderSkeletons();
  await loadConfig();
  await fetchAndRender();
})();

/* ── Event listeners ─────────────────────────────────────────────────────────── */
refreshBtn.addEventListener("click", async () => {
  refreshBtn.disabled = true;
  refreshIcon.style.display = "inline-block";
  await fetch("/api/refresh", { method: "POST" });
  // Poll until status is no longer "polling"
  for (let i = 0; i < 30; i++) {
    await sleep(1500);
    const data = await fetchModels();
    if (data && data.status !== "polling") {
      renderAll(data);
      break;
    }
  }
  refreshBtn.disabled = false;
});

pollSelect.addEventListener("change", async () => {
  const val = pollSelect.value;
  await fetch("/api/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ polling_interval: val }),
  });
  resetAutoRefresh(val);
});

/* ── Data fetching ───────────────────────────────────────────────────────────── */
async function fetchModels() {
  try {
    const r = await fetch("/api/models");
    return await r.json();
  } catch {
    return null;
  }
}

async function fetchAndRender() {
  const data = await fetchModels();
  if (data) renderAll(data);
}

async function loadConfig() {
  try {
    const r = await fetch("/api/config");
    const cfg = await r.json();
    const interval = cfg.polling_interval || "daily";
    pollSelect.value = interval;
    resetAutoRefresh(interval);
  } catch {
    resetAutoRefresh("daily");
  }
}

/* ── Auto-refresh ────────────────────────────────────────────────────────────── */
const INTERVAL_MS = {
  hourly:      60 * 60 * 1000,
  twice_daily: 12 * 60 * 60 * 1000,
  daily:       24 * 60 * 60 * 1000,
};

function resetAutoRefresh(interval) {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  const ms = INTERVAL_MS[interval] || INTERVAL_MS.daily;
  autoRefreshTimer = setInterval(fetchAndRender, ms);
}

/* ── Rendering ───────────────────────────────────────────────────────────────── */
function renderAll(data) {
  updateStatusBar(data);
  const { models } = data;
  if (!models || !Object.keys(models).length) return;

  grid.innerHTML = "";
  for (const key of PROVIDER_ORDER) {
    const provider = models[key];
    if (!provider) continue;
    grid.appendChild(buildCard(key, provider));
  }
}

function buildCard(key, provider) {
  const meta = PROVIDER_META[key] || { icon: "⚪", label: key };
  const hasError = !!provider.error;
  const modelList = provider.models || [];

  const card = el("div", `card provider-${key}`);

  // header
  const hdr  = el("div", "card-header");
  const icon = el("div", "provider-icon");
  icon.innerHTML = meta.icon;
  const name = el("div", "provider-name");
  name.textContent = meta.label;
  const badge = el("span", `card-status ${hasError ? "error" : modelList.length ? "ok" : "loading"}`);
  badge.textContent = hasError ? "error" : modelList.length ? "live" : "empty";
  hdr.append(icon, name, badge);
  card.appendChild(hdr);

  // model list
  if (modelList.length) {
    const ul = el("ul", "model-list");
    for (const m of modelList) {
      const li    = el("li", "model-item");
      const dot   = el("span", "model-bullet");
      const label = el("code", "model-id");
      label.textContent = m.id;
      li.append(dot, label);
      if (m.updated) {
        const ts = el("span", "model-updated");
        ts.textContent = m.updated;
        li.appendChild(ts);
      }
      ul.appendChild(li);
    }
    card.appendChild(ul);
  } else {
    const empty = el("div", "empty-state");
    empty.textContent = hasError
      ? "Could not retrieve models — showing fallback data next refresh."
      : "No models found.";
    card.appendChild(empty);
  }

  return card;
}

function renderSkeletons() {
  grid.innerHTML = "";
  for (const key of PROVIDER_ORDER) {
    const meta = PROVIDER_META[key];
    const card = el("div", `card provider-${key}`);
    const hdr  = el("div", "card-header");
    const icon = el("div", "provider-icon");
    icon.innerHTML = meta.icon;
    const name = el("div", "provider-name");
    name.textContent = meta.label;
    hdr.append(icon, name);
    card.appendChild(hdr);

    const ul = el("ul", "model-list");
    for (let i = 0; i < 4; i++) {
      const li  = el("li", "model-item");
      const dot = el("span", "model-bullet");
      const sk  = el("span", "skeleton");
      sk.style.width = `${55 + Math.random() * 35}%`;
      li.append(dot, sk);
      ul.appendChild(li);
    }
    card.appendChild(ul);
    grid.appendChild(card);
  }
}

function updateStatusBar(data) {
  const { status, last_updated } = data;
  statusDot.className = `dot ${status}`;

  if (last_updated) {
    const d = new Date(last_updated);
    lastUpdated.textContent = `Updated ${timeAgo(d)}`;
    lastUpdated.title = d.toLocaleString();
  } else {
    lastUpdated.textContent = status === "polling" ? "Fetching…" : "Not yet fetched";
  }
}

/* ── Helpers ─────────────────────────────────────────────────────────────────── */
function el(tag, cls) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function timeAgo(date) {
  const secs = Math.floor((Date.now() - date) / 1000);
  if (secs < 60)    return "just now";
  if (secs < 3600)  return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}
