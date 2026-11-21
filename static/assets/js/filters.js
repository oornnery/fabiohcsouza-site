/* /tags: "All tags" shows the less used ones (each tag is a page of its own, rendered by the server).
   /posts: date filter (?m=2026 or ?m=2026-10) hides rows with data-out and shows a "Showing … · show all" note. */
FS.on(function () {
  "use strict";
  var more = document.querySelector("[data-filters-more]");
  if (more) {
    var box = more.closest(".filters"), label = more.textContent;
    var show = function (open) {
      box.classList.toggle("open", open);
      more.setAttribute("aria-expanded", String(open));
      more.textContent = open ? FS.t("Fewer tags") : label;
    };
    more.hidden = false;
    show(box.classList.contains("open"));
    more.addEventListener("click", function () { show(!box.classList.contains("open")); });
  }

  var m = FS.params.get("m");
  if (m && /^\d{4}(-\d{2})?$/.test(m) && document.querySelector("[data-date]")) {
    document.querySelectorAll("[data-date]").forEach(function (r) { r.toggleAttribute("data-out", r.dataset.date.indexOf(m) !== 0); });
    FS.resetPagers();
    var note = document.querySelector(".archive-note");
    if (note) {
      var parts = m.split("-");  // "Sep 2026" / "set. de 2026", from the browser's own locale data
      note.querySelector("[data-archive-label]").textContent = parts[1]
        ? new Date(+parts[0], +parts[1] - 1, 1).toLocaleString(document.documentElement.lang, { month: "short", year: "numeric" })
        : parts[0];
      note.hidden = false;
    }
  }
});
