/* Loaded synchronously in <head> (no defer) so the saved theme applies before first paint (no flash).
   The choice lives in a cookie on the parent domain, so the portfolio and the blog share it (theme.js writes it).
   Everything else lives in deferred scripts. */
(function () {
  document.documentElement.classList.add("js");  // CSS can hide what only works with scripts (the phone menu)
  // also paints the browser bar on phones: <meta name="theme-color"> follows the system until a theme is chosen
  window.setTheme = function (t) {
    document.documentElement.setAttribute("data-theme", t);
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (m) {
      m.media = "";
      m.content = t === "dark" ? "#0c0a09" : "#fafaf9";  // --bg in tokens.css
    });
  };
  // the wordmark types itself once per visit (wordmark.js); the class hides the name before first paint
  try {
    if (!sessionStorage.getItem("fs:typed") && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.documentElement.classList.add("typing");
  } catch (e) { /* no storage: no effect */ }
  var t = (document.cookie.match(/(?:^|; )theme=(light|dark)/) || [])[1];
  if (t) window.setTheme(t);
})();
