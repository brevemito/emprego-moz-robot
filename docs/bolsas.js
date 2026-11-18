/* =========================================================================
   emprego-moz-robot — separador "Bolsas de estudo"
   Lê data/bolsas.json (gerado todos os dias por scraper/bolsas.py) e gere
   os separadores Vagas / Bolsas. Tudo fica dentro de uma função isolada,
   para não colidir com as variáveis globais do app.js (vagas).
   ========================================================================= */

(function () {
  "use strict";

  var BOLSAS_URL =
    "https://raw.githubusercontent.com/brevemito/emprego-moz-robot/main/data/bolsas.json";

  var MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  var SOON_DAYS = 14;

  var allBolsas = [];
  var loaded = false;
  var loading = null;

  function $(id) {
    return document.getElementById(id);
  }

  var el = {
    tabVagas: $("tab-vagas"),
    tabBolsas: $("tab-bolsas"),
    panelVagas: $("panel-vagas"),
    panelBolsas: $("panel-bolsas"),
    countVagas: $("tab-count-vagas"),
    countBolsas: $("tab-count-bolsas"),
    list: $("bolsa-list"),
    resultsCount: $("bolsa-results-count"),
    loadingMsg: $("bolsa-loading"),
    empty: $("bolsa-empty"),
    error: $("bolsa-error"),
    search: $("bolsa-search"),
    level: $("bolsa-level"),
    country: $("bolsa-country"),
    sort: $("bolsa-sort"),
  };

  // Sem o HTML dos separadores (ex.: index.html antigo), não faz nada.
  if (!el.tabVagas || !el.tabBolsas || !el.panelBolsas) return;

  // ---------- separadores ----------

  function selectTab(name, updateHash) {
    var bolsas = name === "bolsas";
    el.tabVagas.setAttribute("aria-selected", String(!bolsas));
    el.tabBolsas.setAttribute("aria-selected", String(bolsas));
    el.tabVagas.tabIndex = bolsas ? -1 : 0;
    el.tabBolsas.tabIndex = bolsas ? 0 : -1;
    el.panelVagas.hidden = bolsas;
    el.panelBolsas.hidden = !bolsas;

    if (updateHash && window.history && window.history.replaceState) {
      window.history.replaceState(null, "", bolsas ? "#bolsas" : "#vagas");
    }
    if (bolsas) load();
  }

  el.tabVagas.addEventListener("click", function () { selectTab("vagas", true); });
  el.tabBolsas.addEventListener("click", function () { selectTab("bolsas", true); });

  // Setas esquerda/direita mudam de separador (padrão de acessibilidade).
  [el.tabVagas, el.tabBolsas].forEach(function (tab) {
    tab.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      var next = tab === el.tabVagas ? el.tabBolsas : el.tabVagas;
      next.focus();
      selectTab(next === el.tabBolsas ? "bolsas" : "vagas", true);
    });
  });

  window.addEventListener("hashchange", function () {
    selectTab(location.hash === "#bolsas" ? "bolsas" : "vagas", false);
  });

  // Contador de vagas no separador: lê o número que o app.js já escreve
  // no quadro ("stat-count"), sem mexer no app.js.
  var statCount = $("stat-count");
  if (statCount && el.countVagas && window.MutationObserver) {
    var syncCount = function () {
      var n = statCount.textContent.trim();
      if (/^\d+$/.test(n)) el.countVagas.textContent = n;
    };
    new MutationObserver(syncCount).observe(statCount, { childList: true, characterData: true, subtree: true });
    syncCount();
  }

  // ---------- dados ----------

  function load() {
    if (loaded || loading) return loading;
    loading = fetch(BOLSAS_URL + "?t=" + Date.now())
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        allBolsas = Array.isArray(data) ? data : (data.bolsas || []);
        loaded = true;
        el.loadingMsg.hidden = true;
        el.countBolsas.textContent = String(allBolsas.length);
        populateFilters();
        applyFilters();
      })
      .catch(function (err) {
        console.error("Falha ao carregar bolsas.json:", err);
        el.loadingMsg.hidden = true;
        el.error.hidden = false;
        loading = null;
      });
    return loading;
  }

  function countriesOf(b) {
    return (b.country || "").split(",").map(function (c) { return c.trim(); }).filter(Boolean);
  }

  function addOptions(select, values) {
    values.forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });
  }

  function uniqueSorted(values) {
    return Array.from(new Set(values)).sort(function (a, b) { return a.localeCompare(b, "pt"); });
  }

  function populateFilters() {
    var levels = [];
    var countries = [];
    allBolsas.forEach(function (b) {
      (b.levels || []).forEach(function (l) { levels.push(l); });
      countriesOf(b).forEach(function (c) { countries.push(c); });
    });
    addOptions(el.level, uniqueSorted(levels));
    addOptions(el.country, uniqueSorted(countries));
  }

  // ---------- filtros ----------

  function applyFilters() {
    var q = el.search.value.trim().toLowerCase();
    var level = el.level.value;
    var country = el.country.value;

    var result = allBolsas.filter(function (b) {
      if (level && (b.levels || []).indexOf(level) === -1) return false;
      if (country && countriesOf(b).indexOf(country) === -1) return false;
      if (q) {
        var hay = [b.title, b.provider, b.summary, b.country].filter(Boolean).join(" ").toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });

    // Programas em destaque (data/bolsas_fixas.json) ficam sempre no topo.
    function featuredFirst(a, b) {
      return (b.featured ? 1 : 0) - (a.featured ? 1 : 0);
    }

    if (el.sort.value === "recent") {
      result.sort(function (a, b) {
        return featuredFirst(a, b) || (b.first_seen_at || "").localeCompare(a.first_seen_at || "");
      });
    } else {
      // Prazo mais próximo primeiro; bolsas sem data no fim.
      result.sort(function (a, b) {
        var f = featuredFirst(a, b);
        if (f) return f;
        if (!a.deadline && !b.deadline) return a.title.localeCompare(b.title, "pt");
        if (!a.deadline) return 1;
        if (!b.deadline) return -1;
        return a.deadline.localeCompare(b.deadline);
      });
    }

    render(result);
  }

  // ---------- apresentação ----------

  function daysLeft(iso) {
    if (!iso) return null;
    var parts = iso.split("-").map(Number);
    var deadline = new Date(parts[0], parts[1] - 1, parts[2]);
    var now = new Date();
    var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.round((deadline - today) / 86400000);
  }

  function formatDate(iso) {
    var p = iso.split("-").map(Number);
    return p[2] + " " + MESES[p[1] - 1] + " " + p[0];
  }

  function deadlineLabel(b) {
    if (!b.deadline) {
      if (b.featured) return { text: b.deadline_text || "Próxima edição: a anunciar", soon: false };
      return { text: "Prazo: ver no site" + (b.deadline_text ? " (" + b.deadline_text + ")" : ""), soon: false };
    }
    var d = daysLeft(b.deadline);
    var when;
    if (d === null || d < 0) when = "";
    else if (d === 0) when = " · termina hoje";
    else if (d === 1) when = " · falta 1 dia";
    else when = " · faltam " + d + " dias";
    return { text: "Prazo: " + formatDate(b.deadline) + when, soon: d !== null && d >= 0 && d <= SOON_DAYS };
  }

  function span(className, text) {
    var s = document.createElement("span");
    if (className) s.className = className;
    s.textContent = text;
    return s;
  }

  function buildCard(b) {
    var card = document.createElement("article");
    card.className = "job-card bolsa-card" + (b.featured ? " is-featured" : "");

    var main = document.createElement("div");
    main.className = "job-main";

    var title = document.createElement("h2");
    title.className = "job-title";
    title.textContent = b.title || "Bolsa sem título";
    main.appendChild(title);

    var meta = document.createElement("div");
    meta.className = "job-meta";

    var first = true;
    [b.provider, b.country].forEach(function (txt) {
      if (!txt) return;
      if (!first) meta.appendChild(span("sep", "·"));
      meta.appendChild(span("", txt));
      first = false;
    });

    if (b.featured) {
      meta.appendChild(span("job-tag bolsa-featured", "Destaque"));
    }

    (b.levels || []).forEach(function (l) {
      meta.appendChild(span("job-tag bolsa-level", l));
    });

    var dl = deadlineLabel(b);
    meta.appendChild(span("bolsa-deadline" + (dl.soon ? " is-soon" : ""), dl.text));

    main.appendChild(meta);

    if (b.summary) {
      var p = document.createElement("p");
      p.className = "bolsa-summary";
      p.textContent = b.summary;
      main.appendChild(p);
    }

    card.appendChild(main);

    var link = document.createElement("a");
    link.className = "job-apply";
    link.href = b.url || "#";
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "Ver bolsa";
    card.appendChild(link);

    return card;
  }

  function render(items) {
    el.list.innerHTML = "";
    if (items.length === 0) {
      el.empty.hidden = false;
      el.resultsCount.textContent = "";
      return;
    }
    el.empty.hidden = true;
    el.resultsCount.textContent =
      items.length + " bolsa" + (items.length === 1 ? "" : "s") +
      " encontrada" + (items.length === 1 ? "" : "s");

    var frag = document.createDocumentFragment();
    items.forEach(function (b) { frag.appendChild(buildCard(b)); });
    el.list.appendChild(frag);
  }

  var timer;
  el.search.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(applyFilters, 180);
  });
  [el.level, el.country, el.sort].forEach(function (c) {
    c.addEventListener("change", applyFilters);
  });

  // ---------- arranque ----------

  selectTab(location.hash === "#bolsas" ? "bolsas" : "vagas", false);

  // Carrega o número de bolsas logo à entrada (para o contador do
  // separador), mesmo que a pessoa ainda esteja a ver as vagas.
  load();

  // Exposto só para testes automáticos.
  window.__bolsas = { deadlineLabel: deadlineLabel, daysLeft: daysLeft, applyFilters: applyFilters };
})();
