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

let allJobs = [];
let filteredJobs = [];

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

  populateFilters(allJobs);
  updateBoard(allJobs);

  el.search.addEventListener("input", debounce(applyFilters, 180));
  el.filterCategory.addEventListener("change", applyFilters);
  el.filterLocation.addEventListener("change", applyFilters);
  el.sortOrder.addEventListener("change", applyFilters);

  applyFilters();
}

function populateFilters(jobs) {
  const categories = uniqueSorted(jobs.map((j) => j.category).filter(Boolean));
  for (const cat of categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    el.filterCategory.appendChild(opt);
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

  filteredJobs = allJobs.filter((job) => {
    if (category && job.category !== category) return false;

    if (location) {
      const locs = Array.isArray(job.locations) ? job.locations : [];
      if (!locs.includes(location)) return false;
    }

    if (query) {
      const haystack = [job.title, job.company, job.description]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(query)) return false;
    }

    return true;
  });

  if (sort === "recent") {
    filteredJobs.sort((a, b) => {
      const dateA = a.first_seen_at ? new Date(a.first_seen_at).getTime() : 0;
      const dateB = b.first_seen_at ? new Date(b.first_seen_at).getTime() : 0;
      return dateB - dateA;
    });
  } else {
    filteredJobs.sort((a, b) => (b.score || 0) - (a.score || 0));
  }

  render(filteredJobs);
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

  const main = document.createElement("div");
  main.className = "job-main";

  const title = document.createElement("h2");
  title.className = "job-title";
  title.textContent = job.title || "Vaga sem título";
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
