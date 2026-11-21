/* Shared namespace for the other scripts. Loaded first (defer keeps the order).
   FS.t(text)       translate a UI string, from <meta name="fs:strings"> (Portuguese pages)
   FS.on(fn)        run fn when the DOM is ready
   FS.params        URLSearchParams of the current page
   FS.icon(name)    <svg><use> markup for the sprite in /assets/img/icons.svg
   FS.resetPagers() re-apply "Show more" after a filter changed */
(function () {
  "use strict";
  var sprite = (document.querySelector('meta[name="fs:sprite"]') || {}).content || "/assets/img/icons.svg";
  var strings = {};
  try { strings = JSON.parse((document.querySelector('meta[name="fs:strings"]') || {}).content || "{}"); } catch (e) { /* keep English */ }
  window.FS = {
    t: function (s) { return strings[s] || s; },
    on: function (fn) {
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
      else fn();
    },
    params: new URLSearchParams(location.search),
    icon: function (name) {
      return '<svg class="icon" aria-hidden="true"><use href="' + sprite + "#i-" + name + '"/></svg>';
    },
    resetPagers: function () {
      document.querySelectorAll("[data-pager]").forEach(function (p) { if (p.pager) p.pager.reset(); });
    },
  };
})();
