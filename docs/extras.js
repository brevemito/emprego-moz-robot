/* =========================================================================
   emprego-moz-robot — funcionalidades para fazer as pessoas voltarem
   - Guardar vagas e bolsas (ficam neste aparelho) + painel "Guardadas"
   - Partilhar no WhatsApp com um toque
   - Etiqueta "Novo" e contador de novidades desde a última visita
   - Barra discreta para seguir o canal Brevemito no WhatsApp
   - Botão "voltar ao topo" e navegação do cabeçalho
   Não altera o app.js nem o bolsas.js: lê os cartões que eles desenham.
   ========================================================================= */

(function () {
  "use strict";

  var KEY_SAVED = "bm_saved_v1";
  var KEY_LAST_VISIT = "bm_last_visit";
  var KEY_BAR_CLOSED = "bm_channel_bar_closed";
  var BAR_SNOOZE_DAYS = 7;
  var DAY = 86400000;
  var PAGE_URL = "https://vagas.brevemito.com/";

  // ---------- armazenamento seguro (pode falhar em modo privado) ----------

  function readJSON(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { /* sem armazenamento: a funcionalidade fica só nesta visita */ }
  }

  function $(id) { return document.getElementById(id); }

  // Só links normais (http/https); qualquer outro esquema fica "#".
  function safeUrl(u) {
    try {
      var x = new URL(u, location.href);
      return x.protocol === "https:" || x.protocol === "http:" ? x.href : "#";
    } catch (e) {
      return "#";
    }
  }

  // ---------- última visita ----------
  // Lida uma vez à entrada; só é actualizada quando a pessoa sai, para que
  // as etiquetas "Novo" se mantenham durante toda a visita.

  var now = Date.now();
  var lastVisit = readJSON(KEY_LAST_VISIT, null);
  var newSince = typeof lastVisit === "number" ? lastVisit : now - DAY;
  var firstVisit = typeof lastVisit !== "number";

  function rememberVisit() { writeJSON(KEY_LAST_VISIT, Date.now()); }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") rememberVisit();
  });
  window.addEventListener("pagehide", rememberVisit);

  function isNew(card) {
    var t = Date.parse(card.dataset.firstSeen || "");
    return !isNaN(t) && t > newSince;
  }

  // ---------- guardados ----------

  var saved = readJSON(KEY_SAVED, []);
  if (!Array.isArray(saved)) saved = [];

  function isSaved(url) {
    return saved.some(function (s) { return s.url === url; });
  }

  function toggleSaved(item) {
    if (isSaved(item.url)) {
      saved = saved.filter(function (s) { return s.url !== item.url; });
      toast("Removida das guardadas");
    } else {
      saved.unshift(item);
      toast("Guardada. Encontra-a em “Guardadas”, no topo.");
    }
    writeJSON(KEY_SAVED, saved);
    syncSaved();
  }

  function syncSaved() {
    var count = $("saved-count");
    if (count) {
      count.textContent = String(saved.length);
      count.hidden = saved.length === 0;
    }
    // Actualiza os botões dos cartões visíveis
    document.querySelectorAll(".card-save").forEach(function (btn) {
      var on = isSaved(btn.dataset.url);
      btn.setAttribute("aria-pressed", String(on));
      btn.querySelector(".card-save-label").textContent = on ? "Guardada" : "Guardar";
    });
    renderDrawer();
  }

  // ---------- ícones ----------

  var ICON_SAVE = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>';
  var ICON_WA = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.7 14.9L2 22l5.3-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3.1.8.8-3-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3a.5.5 0 0 0 0-.5l-.8-1.9c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3z"/></svg>';

  // ---------- decorar cartões ----------

  function shareText(card) {
    var kind = card.dataset.kind === "bolsa" ? "Bolsa de estudo" : "Vaga";
    var org = card.dataset.org ? " — " + card.dataset.org : "";
    var section = card.dataset.kind === "bolsa" ? "#bolsas" : "#vagas";
    return kind + ": " + card.dataset.title + org + "\n" + (card.dataset.page || card.dataset.url) +
      "\n\nMais vagas e bolsas para moçambicanos: " + PAGE_URL + section;
  }

  function decorate(card) {
    if (card.dataset.decorated || !card.dataset.url) return;
    card.dataset.decorated = "1";

    var main = card.querySelector(".job-main");
    if (!main) return;

    if (isNew(card)) {
      card.classList.add("is-new");
      var title = card.querySelector(".job-title");
      if (title) {
        var badge = document.createElement("span");
        badge.className = "badge-new";
        badge.textContent = "Novo";
        title.insertBefore(badge, title.firstChild);
      }
    }

    var actions = document.createElement("div");
    actions.className = "card-actions";

    var save = document.createElement("button");
    save.type = "button";
    save.className = "card-action card-save";
    save.dataset.url = card.dataset.url;
    save.setAttribute("aria-pressed", String(isSaved(card.dataset.url)));
    save.innerHTML = ICON_SAVE + '<span class="card-save-label"></span>';
    save.querySelector(".card-save-label").textContent = isSaved(card.dataset.url) ? "Guardada" : "Guardar";
    save.addEventListener("click", function () {
      toggleSaved({
        url: card.dataset.url,
        title: card.dataset.title,
        org: card.dataset.org,
        kind: card.dataset.kind,
        savedAt: Date.now(),
      });
    });

    var share = document.createElement("a");
    share.className = "card-action card-share";
    share.href = "https://wa.me/?text=" + encodeURIComponent(shareText(card));
    share.target = "_blank";
    share.rel = "noopener";
    share.innerHTML = ICON_WA + "<span>Partilhar</span>";
    share.setAttribute("aria-label", "Partilhar no WhatsApp: " + card.dataset.title);

    actions.appendChild(save);
    actions.appendChild(share);
    main.appendChild(actions);
  }

  function decorateAll(list) {
    list.querySelectorAll(".job-card").forEach(decorate);
    updateNewCount();
  }

  // Conta as novidades (vagas + bolsas) para o quadro do topo.
  var newCounts = { vaga: 0, bolsa: 0 };
  function updateNewCount() {
    var stat = $("stat-new");
    if (!stat) return;
    ["vaga", "bolsa"].forEach(function (kind) {
      var list = $(kind === "vaga" ? "job-list" : "bolsa-list");
      if (!list) return;
      var cards = list.querySelectorAll('.job-card[data-kind="' + kind + '"]');
      // Só actualiza quando a lista está completa (sem filtros), para o
      // número não mudar quando a pessoa pesquisa.
      if (!isUnfiltered(kind)) return;
      var n = 0;
      cards.forEach(function (c) { if (isNew(c)) n += 1; });
      newCounts[kind] = n;
    });
    stat.textContent = String(newCounts.vaga + newCounts.bolsa);
    var label = $("stat-new-label");
    if (label) label.textContent = firstVisit ? "Novas nas últimas 24 horas" : "Novas desde a sua última visita";
  }

  function isUnfiltered(kind) {
    var ids = kind === "vaga"
      ? ["search-input", "filter-category", "filter-location", "filter-level"]
      : ["bolsa-search", "bolsa-level", "bolsa-country"];
    return ids.every(function (id) { var e = $(id); return !e || !e.value; });
  }

  ["job-list", "bolsa-list"].forEach(function (id) {
    var list = $(id);
    if (!list) return;
    decorateAll(list);
    if (window.MutationObserver) {
      new MutationObserver(function () { decorateAll(list); })
        .observe(list, { childList: true });
    }
  });

  // ---------- painel "Guardadas" ----------

  var drawer = $("saved-drawer");
  var openBtn = $("saved-open");
  var lastFocus = null;

  function renderDrawer() {
    var list = $("saved-list");
    var empty = $("saved-empty");
    if (!list) return;
    list.innerHTML = "";
    saved.forEach(function (s) {
      var li = document.createElement("li");
      li.className = "saved-item";

      var info = document.createElement("a");
      info.href = safeUrl(s.url);
      info.target = "_blank";
      info.rel = "noopener";
      info.className = "saved-link";
      var kind = document.createElement("span");
      kind.className = "saved-kind";
      kind.textContent = s.kind === "bolsa" ? "Bolsa" : "Vaga";
      var t = document.createElement("span");
      t.className = "saved-title";
      t.textContent = s.title;
      var o = document.createElement("span");
      o.className = "saved-org";
      o.textContent = s.org || "";
      info.appendChild(kind);
      info.appendChild(t);
      info.appendChild(o);

      var rm = document.createElement("button");
      rm.type = "button";
      rm.className = "icon-btn";
      rm.setAttribute("aria-label", "Remover " + s.title);
      rm.innerHTML = "&times;";
      rm.addEventListener("click", function () { toggleSaved(s); });

      li.appendChild(info);
      li.appendChild(rm);
      list.appendChild(li);
    });
    if (empty) empty.hidden = saved.length > 0;
  }

  function openDrawer() {
    if (!drawer) return;
    lastFocus = document.activeElement;
    drawer.hidden = false;
    document.body.classList.add("no-scroll");
    var close = drawer.querySelector(".drawer-head [data-close]");
    if (close) close.focus();
  }

  function closeDrawer() {
    if (!drawer || drawer.hidden) return;
    drawer.hidden = true;
    document.body.classList.remove("no-scroll");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  if (openBtn) openBtn.addEventListener("click", openDrawer);
  if (drawer) {
    drawer.addEventListener("click", function (e) {
      if (e.target.closest("[data-close]")) closeDrawer();
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDrawer();
  });

  // ---------- aviso rápido (toast) ----------

  var toastTimer;
  function toast(msg) {
    var t = $("toast");
    if (!t) return;
    t.textContent = msg;
    t.hidden = false;
    t.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      t.classList.remove("is-visible");
      setTimeout(function () { t.hidden = true; }, 250);
    }, 2600);
  }

  // ---------- barra do canal WhatsApp e voltar ao topo ----------

  var bar = $("channel-bar");
  var barClosedAt = readJSON(KEY_BAR_CLOSED, 0);
  var barAllowed = !(typeof barClosedAt === "number" && now - barClosedAt < BAR_SNOOZE_DAYS * DAY);
  var toTop = $("back-to-top");

  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    var depth = y / Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    if (bar && barAllowed) bar.hidden = depth < 0.3;
    if (toTop) toTop.hidden = y < 900;
  }

  var ticking = false;
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () { onScroll(); ticking = false; });
  }, { passive: true });

  var barClose = $("channel-bar-close");
  if (barClose) {
    barClose.addEventListener("click", function () {
      barAllowed = false;
      bar.hidden = true;
      writeJSON(KEY_BAR_CLOSED, Date.now());
    });
  }

  if (toTop) {
    toTop.addEventListener("click", function () {
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    });
  }

  // ---------- navegação: ligações #vagas / #bolsas levam aos separadores ----------

  function markNav() {
    var current = location.hash === "#bolsas" ? "bolsas" : "vagas";
    document.querySelectorAll(".site-nav [data-nav]").forEach(function (a) {
      if (a.dataset.nav === current) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }

  document.addEventListener("click", function (e) {
    var link = e.target.closest && e.target.closest("a[data-nav]");
    if (!link) return;
    e.preventDefault();
    var target = link.dataset.nav;
    if (location.hash !== "#" + target) location.hash = target; // o bolsas.js troca o separador
    var tabs = document.querySelector(".tabs");
    if (tabs) {
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      var top = tabs.getBoundingClientRect().top + window.pageYOffset - 70;
      window.scrollTo({ top: top, behavior: reduce ? "auto" : "smooth" });
    }
    markNav();
  });
  window.addEventListener("hashchange", markNav);

  // Os separadores também actualizam a navegação do topo.
  ["tab-vagas", "tab-bolsas"].forEach(function (id) {
    var tab = $(id);
    if (tab) tab.addEventListener("click", function () { setTimeout(markNav, 0); });
  });

  var year = $("footer-year");
  if (year) year.textContent = String(new Date().getFullYear());

  markNav();
  syncSaved();
  onScroll();
})();
