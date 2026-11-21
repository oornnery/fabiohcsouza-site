/* Post page: the copy-link button, the table of contents scroll spy
   (highlights the section in view) and, on phones, the top bar: section name + reading progress (--read, 0..1). */
FS.on(function () {
  "use strict";
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.hidden = !navigator.clipboard;  // http:// on a LAN address: no clipboard API, no button
    b.addEventListener("click", function () {
      navigator.clipboard.writeText(b.dataset.copy).then(function () {
        b.classList.add("done");
        setTimeout(function () { b.classList.remove("done"); }, 1600);
      });
    });
  });

  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
  if (!links.length) return;
  var targets = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); }).filter(Boolean);
  var bar = document.querySelector(".toc-bar");
  var name = bar && bar.querySelector("[data-toc-current]");
  var article = document.querySelector("article");
  function spy() {
    var current = targets[0];
    targets.forEach(function (t) { if (t.getBoundingClientRect().top < innerHeight * 0.3) current = t; });
    links.forEach(function (a) {
      var on = a.getAttribute("href") === "#" + current.id;
      a.classList.toggle("active", on);
      if (on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
    });
    if (!bar) return;
    name.textContent = current.textContent;
    var box = article.getBoundingClientRect();
    var read = Math.min(1, Math.max(0, -box.top / Math.max(1, box.height - innerHeight)));
    bar.style.setProperty("--read", read.toFixed(3));  // CSSOM, allowed by the CSP (no inline style attribute)
  }
  if (bar) bar.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", function () { bar.open = false; }); });
  addEventListener("scroll", spy, { passive: true });
  spy();
});
