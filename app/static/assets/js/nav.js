/* Phone menu: the button next to the theme toggle opens and closes the site links (layout.css hides them on
   phones once this runs). Esc or a click outside closes it; focus returns to the button. */
FS.on(function () {
  "use strict";
  var header = document.querySelector(".site-header");
  var button = header && header.querySelector(".menu-toggle");
  if (!button) return;
  function set(open, focus) {
    header.classList.toggle("open", open);
    button.setAttribute("aria-expanded", String(open));
    if (open) { var first = header.querySelector(".nav a"); if (first) first.focus(); } else if (focus) button.focus();
  }
  button.addEventListener("click", function () { set(!header.classList.contains("open"), true); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && header.classList.contains("open")) set(false, true); });
  document.addEventListener("click", function (e) { if (header.classList.contains("open") && !header.contains(e.target)) set(false, false); });
});
