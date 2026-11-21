/* "Show more" pagination.
   Markup: <div data-pager data-page-size="6" [data-page-size-sm="1"] [data-unit="years"]>
             … [data-item] rows (optionally inside [data-year] groups) …
             <button data-more hidden>Show more</button>
           </div>
   Rows with data-out (filtered by tag/date) or data-miss (search) never count. Empty groups hide.
   Also: #anchors that point into a hidden row reveal it (e.g. /timeline#y2023). */
FS.on(function () {
  "use strict";
  function visible(pager) {
    return Array.prototype.filter.call(pager.querySelectorAll("[data-item]"), function (i) {
      return !i.hasAttribute("data-out") && !i.hasAttribute("data-miss");
    });
  }

  document.querySelectorAll("[data-pager]").forEach(function (pager) {
    var small = innerWidth < 560 && Number(pager.dataset.pageSizeSm);
    var size = small || Number(pager.dataset.pageSize) || 5;
    var btn = pager.querySelector("[data-more]");
    var shown = size;
    var empty = document.createElement("p");
    empty.className = "empty";
    empty.hidden = true;
    pager.append(empty);

    function render() {
      var pool = visible(pager);
      pager.querySelectorAll("[data-item]").forEach(function (i) { i.hidden = true; });
      pool.slice(0, shown).forEach(function (i) { i.hidden = false; });
      pager.querySelectorAll("[data-year]").forEach(function (g) { g.hidden = !g.querySelector("[data-item]:not([hidden])"); });
      empty.textContent = FS.t("Nothing matches.");
      empty.hidden = pool.length > 0;
      if (!btn) return;
      var rest = pool.length - shown;
      btn.hidden = rest <= 0;
      var unit = pager.dataset.unit ? " " + FS.t(pager.dataset.unit) : "";
      btn.textContent = FS.t("Show more") + " ";
      var count = document.createElement("span");
      count.className = "faint";
      count.textContent = "(" + rest + unit + ")";
      btn.append(count);
    }

    if (btn) btn.addEventListener("click", function () { shown += size; render(); });
    pager.pager = {
      render: render,
      reset: function () { shown = size; render(); },
      reveal: function (el) {
        var idx = visible(pager).findIndex(function (i) { return i === el || i.contains(el); });
        if (idx >= shown) { shown = Math.ceil((idx + 1) / size) * size; render(); }
      },
    };
    render();
  });

  function goHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    var pager = el && el.closest("[data-pager]");
    if (pager && pager.pager) { pager.pager.reveal(el); el.scrollIntoView(); }
  }
  addEventListener("hashchange", goHash);
  goHash();
});
