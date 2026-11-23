/* =========================================================================
   emprego-moz-robot — site de vagas
   Lê data/jobs.json directamente do repositório (via raw.githubusercontent
   .com, para funcionar independentemente de onde este site está publicado)
   e permite procurar, filtrar por categoria/localização e ordenar.
   ========================================================================= */

const JOBS_URL =
  "https://raw.githubusercontent.com/brevemito/emprego-moz-robot/main/data/jobs.json";

// Cores por categoria, para as etiquetas dos cartões. Inspiradas na
// paleta viva usada em capulanas e nos murais de Malangatana (vermelhos,
// ocres, índigos, verdes profundos). Mantidas em sincronia (na medida do
// possível) com scraper/job_category.py. Todas testadas para dar pelo
// menos 4.5:1 de contraste com o texto creme (--cream) das etiquetas,
// conforme WCAG AA para texto normal.
const CATEGORY_COLORS = {
  "Estágios": "#1B6B6B",
   "Educação e Formação": "#2E5E8C",
  "Electricidade e Energia": "#8A5A00",
  "Saúde": "#C1272D",
  "Segurança e HSE": "#7A2635",
  "Tecnologia da Informação": "#2F6B4A",
  "Financeiro e Contabilidade": "#5B3A73",
  "Recursos Humanos": "#8B4225",
  "Comercial e Vendas": "#2D7050",
  "Logística e Transportes": "#9A5D1A",
  "Engenharia": "#1B4B6B",
  "Construção e Manutenção Técnica": "#6B5B1F",
  "Hotelaria e Restauração": "#A6431F",
  "Gestão e Direcção": "#6B2545",
  "Consultoria e Organizações Internacionais": "#1E3F5C",
  "Outros": "#34383B",
};

// Níveis (ver scraper/job_level.py), pela ordem em que aparecem no filtro.
const LEVELS = [
  ["basico", "12.ª classe ou menos"],
  ["tecnico", "Técnico médio"],
  ["estagio", "Estágio / recém-formado"],
  ["licenciatura", "Licenciatura"],
  ["experiente", "Experiente / sénior"],
];
const KEY_SEARCH = "bm_saved_search_v1";
const KEY_LAST_VISIT = "bm_last_visit"; // o mesmo usado pelo extras.js

let allJobs = [];
let filteredJobs = [];
let showIntl = false;

const el = {
  jobList: document.getElementById("job-list"),
  resultsCount: document.getElementById("results-count"),
  emptyState: document.getElementById("empty-state"),
  errorState: document.getElementById("error-state"),
  loadingMessage: document.getElementById("loading-message"),
  search: document.getElementById("search-input"),
  filterCategory: document.getElementById("filter-category"),
  filterLocation: document.getElementById("filter-location"),
  sortOrder: document.getElementById("sort-order"),
  statCount: document.getElementById("stat-count"),
  statUpdated: document.getElementById("stat-updated"),
};

// Lido antes de o extras.js actualizar a data da visita.
const lastVisitAtLoad = (() => {
  try { return JSON.parse(localStorage.getItem(KEY_LAST_VISIT)); } catch (e) { return null; }
})();

init();

async function init() {
  try {
    const response = await fetch(`${JOBS_URL}?t=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    allJobs = await response.json();
  } catch (err) {
    console.error("Falha ao carregar jobs.json:", err);
    el.loadingMessage.hidden = true;
    el.errorState.hidden = false;
    return;
  }

  el.loadingMessage.hidden = true;

  buildExtraControls();
  populateFilters(allJobs);
  updateBoard(allJobs);

  el.search.addEventListener("input", debounce(applyFilters, 180));
  el.filterCategory.addEventListener("change", applyFilters);
  el.filterLocation.addEventListener("change", applyFilters);
  el.sortOrder.addEventListener("change", applyFilters);
  el.filterLevel.addEventListener("change", applyFilters);
  [el.filterCategory, el.filterLocation, el.filterLevel].forEach((s) =>
    s.addEventListener("change", () => { if (s.value) track("filtro-" + s.id.replace("filter-", ""), s.value); })
  );

  applyFilters();
  showSavedSearchAlert();
}

/* ---------- controlos novos: nível, internacionais, pesquisa guardada ---------- */

function buildExtraControls() {
  const controls = el.search.closest(".controls");

  el.filterLevel = document.createElement("select");
  el.filterLevel.id = "filter-level";
  el.filterLevel.className = "control";
  el.filterLevel.setAttribute("aria-label", "Filtrar pelo meu nível");
  el.filterLevel.innerHTML = '<option value="">Para o meu nível: todos</option>';
  controls.insertBefore(el.filterLevel, el.sortOrder);

  const row = document.createElement("div");
  row.className = "bm-chips";
  const intlCount = allJobs.filter((j) => j.audience === "internacional").length;
  row.innerHTML =
    '<button type="button" class="bm-chip" id="bm-intl" aria-pressed="false">🌍 Internacionais e ONU <span>' + intlCount + "</span></button>" +
    '<button type="button" class="bm-chip" id="bm-save-search">🔔 Guardar esta pesquisa</button>' +
    '<button type="button" class="bm-chip bm-install" id="bm-install" hidden>📲 Instalar a app</button>';
  controls.insertAdjacentElement("afterend", row);

  const alert = document.createElement("div");
  alert.id = "bm-search-alert";
  alert.className = "bm-alert";
  alert.hidden = true;
  row.insertAdjacentElement("afterend", alert);

  document.getElementById("bm-intl").addEventListener("click", (e) => {
    showIntl = !showIntl;
    e.currentTarget.setAttribute("aria-pressed", String(showIntl));
    if (showIntl) track("ver-internacionais");
    applyFilters();
  });
  document.getElementById("bm-save-search").addEventListener("click", saveSearch);
  setupInstall(document.getElementById("bm-install"));
}

function currentSearch() {
  return {
    q: el.search.value.trim(),
    category: el.filterCategory.value,
    location: el.filterLocation.value,
    level: el.filterLevel.value,
  };
}

function describeSearch(s) {
  const parts = [s.q && "«" + s.q + "»", s.level && levelLabel(s.level), s.category, s.location].filter(Boolean);
  return parts.join(" · ");
}

function saveSearch() {
  const s = currentSearch();
  if (!describeSearch(s)) {
    toastMsg("Escolha primeiro uma pesquisa ou filtros (ex.: «electricista» e Maputo).");
    return;
  }
  try { localStorage.setItem(KEY_SEARCH, JSON.stringify(s)); } catch (e) { /* sem armazenamento */ }
  track("guardar-pesquisa", describeSearch(s));
  toastMsg("Pesquisa guardada. Na próxima visita mostramos as vagas novas para: " + describeSearch(s));
}

function showSavedSearchAlert() {
  let s = null;
  try { s = JSON.parse(localStorage.getItem(KEY_SEARCH)); } catch (e) { s = null; }
  if (!s || !describeSearch(s)) return;
  const since = typeof lastVisitAtLoad === "number" ? lastVisitAtLoad : Date.now() - 86400000;
  const matches = allJobs.filter((j) => matchesSearch(j, s, true));
  const fresh = matches.filter((j) => Date.parse(j.first_seen_at || "") > since);
  const box = document.getElementById("bm-search-alert");
  box.innerHTML = "";
  const p = document.createElement("p");
  p.textContent = fresh.length
    ? "🔔 " + fresh.length + " vaga" + (fresh.length === 1 ? " nova" : "s novas") + " para a sua pesquisa (" + describeSearch(s) + ") desde a última visita."
    : "🔔 A sua pesquisa (" + describeSearch(s) + ") tem " + matches.length + " vaga" + (matches.length === 1 ? "" : "s") + ". Nenhuma nova desde a última visita.";
  const go = document.createElement("button");
  go.type = "button";
  go.className = "bm-chip";
  go.textContent = "Ver";
  go.addEventListener("click", () => {
    el.search.value = s.q || "";
    el.filterCategory.value = s.category || "";
    el.filterLocation.value = s.location || "";
    el.filterLevel.value = s.level || "";
    track("abrir-pesquisa-guardada");
    applyFilters();
    el.resultsCount.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  const del = document.createElement("button");
  del.type = "button";
  del.className = "bm-chip";
  del.textContent = "Apagar";
  del.addEventListener("click", () => {
    try { localStorage.removeItem(KEY_SEARCH); } catch (e) { /* nada */ }
    box.hidden = true;
  });
  box.append(p, go, del);
  box.hidden = false;
}

function levelLabel(code) {
  const f = LEVELS.find((l) => l[0] === code);
  return f ? f[1] : "";
}

function toastMsg(msg) {
  const t = document.getElementById("toast");
  if (!t) { alert(msg); return; }
  t.textContent = msg;
  t.hidden = false;
  t.classList.add("is-visible");
  clearTimeout(toastMsg.timer);
  toastMsg.timer = setTimeout(() => { t.classList.remove("is-visible"); t.hidden = true; }, 4200);
}

/* ---------- aplicação instalável (PWA) ---------- */

let installEvent = null;
function setupInstall(btn) {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => { /* sem app offline */ });
  }
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    installEvent = e;
    btn.hidden = false;
  });
  btn.addEventListener("click", async () => {
    if (!installEvent) return;
    installEvent.prompt();
    const choice = await installEvent.userChoice;
    track("instalar-app", choice && choice.outcome);
    installEvent = null;
    btn.hidden = true;
  });
}

/* ---------- estatísticas (GoatCounter, sem cookies) ---------- */

function track(name, title) {
  try {
    if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count({ path: "evento-" + name, title: title || name, event: true });
    }
  } catch (e) { /* estatística opcional */ }
}

document.addEventListener("click", (e) => {
  const a = e.target.closest && e.target.closest(".job-apply, .card-share, .card-save, .job-title a");
  if (!a) return;
  const card = a.closest(".job-card");
  const what = card ? card.dataset.title : "";
  if (a.classList.contains("job-apply")) track("candidatar", what);
  else if (a.classList.contains("card-share")) track("partilhar-whatsapp", what);
  else if (a.classList.contains("card-save")) track("guardar", what);
  else track("abrir-vaga", what);
});

function populateFilters(jobs) {
  const categories = uniqueSorted(jobs.map((j) => j.category).filter(Boolean));
  for (const cat of categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    el.filterCategory.appendChild(opt);
  }

  for (const [code, label] of LEVELS) {
    const n = jobs.filter((j) => j.level === code).length;
    if (!n) continue;
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${label} (${n})`;
    el.filterLevel.appendChild(opt);
  }

  const locations = uniqueSorted(
    jobs.flatMap((j) => (Array.isArray(j.locations) ? j.locations : []))
  );
  for (const loc of locations) {
    const opt = document.createElement("option");
    opt.value = loc;
    opt.textContent = loc;
    el.filterLocation.appendChild(opt);
  }
}

function applyFilters() {
  const query = el.search.value.trim().toLowerCase();
  const category = el.filterCategory.value;
  const location = el.filterLocation.value;
  const sort = el.sortOrder.value;
  const s = { q: query, category, location, level: el.filterLevel.value };

  // As vagas internacionais (ONU, consultorias) ficam à parte, salvo se a
  // pessoa as pedir, procurar por elas ou escolher a categoria delas.
  const intlOn = showIntl || category === "Consultoria e Organizações Internacionais";
  filteredJobs = allJobs.filter((job) => {
    if (!intlOn && !query && job.audience === "internacional") return false;
    return matchesSearch(job, s, false);
  });

  if (sort === "recent") {
    filteredJobs.sort((a, b) => {
      const dateA = a.first_seen_at ? new Date(a.first_seen_at).getTime() : 0;
      const dateB = b.first_seen_at ? new Date(b.first_seen_at).getTime() : 0;
      return dateB - dateA;
    });
  } else {
    filteredJobs.sort((a, b) => (b.rank ?? b.score ?? 0) - (a.rank ?? a.score ?? 0));
  }

  render(filteredJobs);
  if (!intlOn && !query) {
    const hidden = allJobs.filter((j) => j.audience === "internacional" && matchesSearch(j, s, false)).length;
    if (hidden && filteredJobs.length) el.resultsCount.textContent += ` · mais ${hidden} internacionais no botão 🌍`;
    if (hidden && !filteredJobs.length) { el.emptyState.hidden = true; el.resultsCount.textContent = `Há ${hidden} vaga(s) internacionais para esta pesquisa: toque em 🌍 para as ver.`; }
  }
}

function matchesSearch(job, s, skipIntl) {
  if (skipIntl && job.audience === "internacional" && s.category !== "Consultoria e Organizações Internacionais") return false;
  if (s.category && job.category !== s.category) return false;
  if (s.level && job.level !== s.level) return false;
  if (s.location) {
    const locs = Array.isArray(job.locations) ? job.locations : [];
    if (!locs.includes(s.location)) return false;
  }
  if (s.q) {
    const haystack = [job.title, job.company, job.description].filter(Boolean).join(" ").toLowerCase();
    if (!haystack.includes(s.q.toLowerCase())) return false;
  }
  return true;
}

function render(jobs) {
  el.jobList.innerHTML = "";

  if (jobs.length === 0) {
    el.emptyState.hidden = false;
    el.resultsCount.textContent = "";
    return;
  }

  el.emptyState.hidden = true;
  el.resultsCount.textContent = `${jobs.length} vaga${jobs.length === 1 ? "" : "s"} encontrada${jobs.length === 1 ? "" : "s"}`;

  const fragment = document.createDocumentFragment();

  for (const job of jobs) {
    fragment.appendChild(buildCard(job));
  }

  el.jobList.appendChild(fragment);
}

function buildCard(job) {
  const card = document.createElement("article");
  card.className = "job-card";

  // Dados usados pelo extras.js (guardar, partilhar, "Novo").
  card.dataset.kind = "vaga";
  card.dataset.url = job.url || "";
  card.dataset.title = job.title || "";
  card.dataset.org = job.company || "";
  card.dataset.firstSeen = job.first_seen_at || job.scraped_at || "";
  // Página própria da vaga (gerada pelo robô): usada no título e na partilha.
  card.dataset.page = job.page ? new URL(job.page, location.href).href : "";

  const main = document.createElement("div");
  main.className = "job-main";

  const title = document.createElement("h2");
  title.className = "job-title";
  if (job.page) {
    const link = document.createElement("a");
    link.href = job.page;
    link.textContent = job.title || "Vaga sem título";
    title.appendChild(link);
  } else {
    title.textContent = job.title || "Vaga sem título";
  }
  main.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "job-meta";

  if (job.company) {
    const company = document.createElement("span");
    company.textContent = job.company;
    meta.appendChild(company);
  }

  if (job.location) {
    meta.appendChild(sepSpan());
    const loc = document.createElement("span");
    loc.textContent = job.location;
    meta.appendChild(loc);
  }

  if (job.category) {
    const tag = document.createElement("span");
    tag.className = "job-tag";
    tag.style.setProperty("--tag-color", CATEGORY_COLORS[job.category] || CATEGORY_COLORS["Outros"]);
    tag.textContent = job.category;
    meta.appendChild(tag);
  }

  if (job.level_label) {
    const lv = document.createElement("span");
    lv.className = "job-level";
    lv.textContent = job.level_label;
    meta.appendChild(lv);
  }

  const age = document.createElement("span");
  age.className = "job-age";
  age.textContent = formatAge(job.days_since_first_seen);
  meta.appendChild(age);

  main.appendChild(meta);
  card.appendChild(main);

  const apply = document.createElement("a");
  apply.className = "job-apply";
  apply.href = job.url || "#";
  apply.target = "_blank";
  apply.rel = "noopener";
  apply.textContent = "Candidatar";
  card.appendChild(apply);

  return card;
}

function sepSpan() {
  const s = document.createElement("span");
  s.className = "sep";
  s.textContent = "·";
  return s;
}

function formatAge(days) {
  if (days === null || days === undefined) return "";
  if (days === 0) return "Publicada hoje";
  if (days === 1) return "Publicada há 1 dia";
  return `Publicada há ${days} dias`;
}

function updateBoard(jobs) {
  el.statCount.textContent = jobs.length;

  const timestamps = jobs
    .map((j) => j.last_seen_at || j.scraped_at)
    .filter(Boolean)
    .map((t) => new Date(t).getTime());

  if (timestamps.length === 0) {
    el.statUpdated.textContent = "Sem dados";
    return;
  }

  const mostRecent = new Date(Math.max(...timestamps));
  el.statUpdated.textContent = `Actualizado ${formatRelativeTime(mostRecent)}`;
}

function formatRelativeTime(date) {
  const diffMs = Date.now() - date.getTime();
  const diffHours = Math.round(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) return "há poucos minutos";
  if (diffHours < 24) return `há ${diffHours}h`;

  const diffDays = Math.round(diffHours / 24);
  return `há ${diffDays} dia${diffDays === 1 ? "" : "s"}`;
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b, "pt"));
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
