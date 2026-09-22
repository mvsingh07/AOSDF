// AOSDF Project Docs Site — default header controls (Track P, PJ1-T1).
// Copied verbatim into every project's docs/docs_overrides/aosdf.js.
//
// Three independent, persisted (localStorage) UI controls:
//
// 1. Nav collapse — a small toggle "rail" prepended inside the left navigation
//    sidebar itself (above its own nav tree), which shrinks the sidebar to a
//    slim strip containing just that toggle rather than hiding it completely.
//    This is deliberate: a button placed *inside* an element that gets
//    `display:none` would vanish with it, leaving no way to re-expand. Instead
//    we only hide the sidebar's inner `.md-sidebar__scrollwrap` and shrink the
//    outer `.md-sidebar` to a slim width — the rail (and its button) stays put
//    as a sibling of the (now-hidden) scrollwrap, always visible, always
//    clickable, sitting exactly where the section it controls begins.
// 2. TOC collapse — the same mechanism, mirrored, for the right
//    table-of-contents sidebar.
// 3. Wide view — toggles `data-aosdf-wide` on <html>. Material's own
//    `.md-grid` is `max-width:61rem` centered; removing that cap (aosdf.css)
//    is the entire trick — `.md-content` is already `flex-grow:1`, so it
//    absorbs all the freed width automatically, and the two sidebars (already
//    the first/last flex children of `.md-main__inner`) land at the true
//    viewport edges with no other layout change needed. This is a page-level
//    setting, not tied to one sidebar, so its control stays in the header.
//
// `document$` is Material's own documented RxJS hook that fires on every page
// load, including client-side "instant" navigations — required here since
// instant loading swaps the sidebars' DOM (and this script's own insertions)
// on every navigation, not just on first load.
document$.subscribe(function () {
  var NAV_KEY = "aosdf-nav-collapsed";
  var TOC_KEY = "aosdf-toc-collapsed";
  var WIDE_KEY = "aosdf-wide-view";

  var ICON_CHEVRON_LEFT =
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 6 9 12 15 18"></polyline></svg>';
  var ICON_CHEVRON_RIGHT =
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"></polyline></svg>';
  var ICON_EXPAND =
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>';
  var ICON_HOME =
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"></path><path d="M5.5 10v9a1 1 0 0 0 1 1H17.5a1 1 0 0 0 1-1v-9"></path></svg>';

  function isOn(key) {
    return localStorage.getItem(key) === "1";
  }

  function setPanelState(sidebarEl, rail, collapsed, sideLabel) {
    if (!sidebarEl || !rail) return;
    sidebarEl.toggleAttribute("data-aosdf-collapsed", collapsed);
    var btn = rail.querySelector(".aosdf-panel-toggle-btn");
    if (!btn) return;
    var pointsAwayFromContent = sideLabel === "nav" ? !collapsed : collapsed;
    // Nav (left): open state points left (collapse direction); collapsed points right (expand direction).
    // TOC (right): mirrored.
    var iconForNav = collapsed ? ICON_CHEVRON_LEFT : ICON_CHEVRON_RIGHT;
    var iconForToc = collapsed ? ICON_CHEVRON_RIGHT : ICON_CHEVRON_LEFT;
    btn.innerHTML = sideLabel === "nav" ? iconForNav : iconForToc;
    btn.setAttribute(
      "aria-label",
      (collapsed ? "Expand " : "Collapse ") + (sideLabel === "nav" ? "navigation" : "table of contents")
    );
    btn.title = btn.getAttribute("aria-label");
    void pointsAwayFromContent; // reasoning kept above for the next reader; value itself unused
  }

  function ensureRail(sidebarEl, key, sideLabel) {
    if (!sidebarEl || sidebarEl.querySelector(":scope > .aosdf-panel-rail")) return null;
    var rail = document.createElement("div");
    rail.className = "aosdf-panel-rail aosdf-panel-rail--" + sideLabel;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "aosdf-panel-toggle-btn";
    btn.addEventListener("click", function () {
      var next = !isOn(key);
      localStorage.setItem(key, next ? "1" : "0");
      setPanelState(sidebarEl, rail, next, sideLabel);
    });
    rail.appendChild(btn);
    sidebarEl.insertBefore(rail, sidebarEl.firstChild);
    return rail;
  }

  function applyPanels() {
    var nav = document.querySelector(".md-sidebar--primary");
    var toc = document.querySelector(".md-sidebar--secondary");
    var navRail = ensureRail(nav, NAV_KEY, "nav") || (nav && nav.querySelector(":scope > .aosdf-panel-rail"));
    var tocRail = ensureRail(toc, TOC_KEY, "toc") || (toc && toc.querySelector(":scope > .aosdf-panel-rail"));
    setPanelState(nav, navRail, isOn(NAV_KEY), "nav");
    setPanelState(toc, tocRail, isOn(TOC_KEY), "toc");
  }

  function applyWide() {
    document.documentElement.toggleAttribute("data-aosdf-wide", isOn(WIDE_KEY));
    var btn = document.getElementById("aosdf-wide-toggle");
    if (btn) btn.classList.toggle("is-active", isOn(WIDE_KEY));
  }

  // Footer is pinned via `position: fixed` (aosdf.css) so it stays put while
  // scrolling instead of moving with the document flow. Fixed positioning
  // takes it out of flow entirely, so `.md-main` needs matching bottom
  // padding or the last lines of a page's content would sit hidden behind
  // it — measured here (not hardcoded) so it stays correct if the footer's
  // real height ever changes (e.g. a page gains prev/next footer links).
  function applyFooterOffset() {
    var footer = document.querySelector(".md-footer");
    if (!footer) return;
    document.documentElement.style.setProperty("--aosdf-footer-height", footer.offsetHeight + "px");
  }

  applyPanels();
  applyWide();
  applyFooterOffset();

  if (!window.__aosdfFooterResizeBound) {
    window.__aosdfFooterResizeBound = true;
    window.addEventListener("resize", applyFooterOffset);
  }

  var header = document.querySelector(".md-header__inner");
  if (header && !document.getElementById("aosdf-home-link")) {
    var homeLink = document.createElement("a");
    homeLink.id = "aosdf-home-link";
    homeLink.className = "md-header__button md-icon aosdf-panel-toggle";
    homeLink.href = "/";
    homeLink.title = "Back to home";
    homeLink.setAttribute("aria-label", "Back to home");
    homeLink.innerHTML = ICON_HOME;
    header.insertBefore(homeLink, header.firstChild);
  }

  if (header && !document.getElementById("aosdf-wide-toggle")) {
    var wideBtn = document.createElement("button");
    wideBtn.id = "aosdf-wide-toggle";
    wideBtn.type = "button";
    wideBtn.className = "md-header__button md-icon aosdf-panel-toggle";
    wideBtn.title = "Toggle full-width view";
    wideBtn.setAttribute("aria-label", "Toggle full-width view");
    wideBtn.innerHTML = ICON_EXPAND;
    wideBtn.addEventListener("click", function () {
      localStorage.setItem(WIDE_KEY, isOn(WIDE_KEY) ? "0" : "1");
      applyWide();
    });
    header.appendChild(wideBtn);
    applyWide();
  }
});
