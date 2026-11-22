/* Post page: the like button, the copy-link button, the table of contents scroll spy
   (highlights the section in view) and, on phones, the top bar: section name + reading progress (--read, 0..1). */
FS.on(function () {
  "use strict";
  // like: POST, show the new total; localStorage remembers this browser liked (no cookie, nothing on the server)
  document.querySelectorAll("form[data-like]").forEach(function (form) {
    var key = "liked:" + form.dataset.like;
    var button = form.querySelector("button");
    var count = form.querySelector("[data-like-count]");
    function mark(on) {
      button.disabled = on;
      if (on) button.setAttribute("aria-pressed", "true"); else button.removeAttribute("aria-pressed");
    }
    try { mark(!!localStorage.getItem(key)); } catch (e) { /* storage blocked: the button still works */ }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      mark(true);
      fetch(form.action, { method: "POST", headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function (d) {
          count.textContent = d.likes;
          try { localStorage.setItem(key, "1"); } catch (e) { /* not remembered: fine */ }
        })
        .catch(function () { mark(false); });
    });
  });

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
