/* The header wordmark types its name like a shell command, once per visit: theme-init.js puts .typing on <html>
   (effects.css hides the name and holds the caret still), this types it key by key and removes the class. */
FS.on(function () {
  "use strict";
  var root = document.documentElement, el = document.querySelector(".site-header .wm-name");
  if (!root.classList.contains("typing")) return;
  if (!el) { root.classList.remove("typing"); return; }
  var name = el.textContent, i = 0;
  el.textContent = "";
  el.classList.add("on");
  try { sessionStorage.setItem("fs:typed", "1"); } catch (e) { /* storage full: it types again next page */ }
  (function key() {
    el.textContent = name.slice(0, ++i);
    if (i < name.length) setTimeout(key, 60 + Math.random() * 110);  // uneven, like a person typing
    else root.classList.remove("typing");
  })();
});
