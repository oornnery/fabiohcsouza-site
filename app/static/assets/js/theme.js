/* Light/dark toggle (sun/moon). Starts from the system preference; a click saves the choice in a cookie for the
   parent domain (fabiohcsouza.dev covers blog.fabiohcsouza.dev): one choice for both sites. Functional only:
   read by theme-init.js in this browser, never sent anywhere that uses it. */
FS.on(function () {
  "use strict";
  var root = document.documentElement;
  var host = location.hostname;
  var parent = /^[\d.]+$|^\[/.test(host) ? "" : host.split(".").slice(-2).join(".");  // blog.x.dev -> x.dev; IPs: none
  function save(theme) {
    document.cookie = "theme=" + theme + "; Path=/; Max-Age=31536000; SameSite=Lax" +
      (parent.indexOf(".") > 0 ? "; Domain=" + parent : "") + (location.protocol === "https:" ? "; Secure" : "");
  }
  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.innerHTML = FS.icon("moon").replace('class="icon"', 'class="icon moon"') + FS.icon("sun").replace('class="icon"', 'class="icon sun"');
    btn.addEventListener("click", function () {
      var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      var next = dark ? "light" : "dark";
      window.setTheme(next);
      save(next);
    });
  });
});
