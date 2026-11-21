/* Client-side search over [data-item] rows (title, summary, tags), accent- and case-insensitive.
   Every word must match. "/" focuses the field, Escape or the × button clears it; a live count says how many rows match. ?q=#tag pre-fills it, and tag links
   pointing at this same page fill it instead of reloading. */
FS.on(function () {
  "use strict";
  var input = document.querySelector("[data-search]");
  if (!input) return;
  function norm(t) { return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  var rows = Array.prototype.map.call(document.querySelectorAll("[data-item]"), function (r) { return [r, norm(r.textContent)]; });
  var box = input.closest(".search");
  var clear = box.querySelector("[data-search-clear]");
  var count = box.querySelector("[data-search-count]");

  function run(q) {
    input.value = q;
    var terms = norm(q).split(/\s+/).filter(Boolean);
    rows.forEach(function (pair) {
      pair[0].toggleAttribute("data-miss", !terms.every(function (t) { return pair[1].indexOf(t) !== -1; }));
    });
    FS.resetPagers();
    var n = rows.filter(function (pair) { return !pair[0].hasAttribute("data-miss") && !pair[0].hasAttribute("data-out"); }).length;
    count.textContent = terms.length ? n + " " + (n === 1 ? FS.t("result") : FS.t("results")) : "";
    clear.hidden = !q;
    box.classList.toggle("has-value", !!q);
  }

  clear.addEventListener("click", function () { run(""); input.focus(); });
  box.addEventListener("click", function (e) { if (!e.target.closest("button")) input.focus(); });

  input.addEventListener("input", function () { run(input.value); });
  if (FS.params.get("q")) run(FS.params.get("q").slice(0, 200));

  document.addEventListener("click", function (e) {
    var a = e.target.closest("a.tag-link");
    if (!a) return;
    var url = new URL(a.href, location.href);
    if (url.pathname !== location.pathname || !url.searchParams.has("q")) return;
    e.preventDefault();
    run(url.searchParams.get("q"));
    history.replaceState(null, "", url.search);
    input.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  document.addEventListener("keydown", function (e) {
    var tag = (document.activeElement || {}).tagName || "";
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) { e.preventDefault(); input.focus(); }
    if (e.key === "Escape" && document.activeElement === input) { run(""); input.blur(); }
  });
});
