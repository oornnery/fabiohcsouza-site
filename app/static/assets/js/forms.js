/* Forms: contact and newsletter.
   <form data-form action="/api/contact" method="post">: posts JSON to `action`; without JavaScript it is a plain POST.
   Validation messages appear under each field; the honeypot field "website" silently drops bots.
   The server validates everything again: this is UX, not security. */
FS.on(function () {
  "use strict";
  function msg(el) {
    var v = el.validity;
    if (v.valueMissing) return FS.t("Required.");
    if (v.typeMismatch) return FS.t("Enter a valid email.");
    if (v.tooShort) return FS.t("A bit more, please.");
    if (v.tooLong) return FS.t("Too long.");
    return "";
  }

  function check(el) {
    var field = el.closest(".field");
    var text = msg(el);
    el.setAttribute("aria-invalid", text ? "true" : "false");
    if (!field) return !text;
    field.classList.toggle("invalid", !!text);
    var err = field.querySelector(".err");
    if (text && !err) {
      err = document.createElement("small");
      err.className = "err";
      err.id = (el.id || el.name) + "-err";
      el.setAttribute("aria-describedby", err.id);
      field.append(err);
    }
    if (err) err.textContent = text;
    return !text;
  }

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    var fields = Array.prototype.slice.call(form.querySelectorAll("input:not([name=website]):not([type=hidden]), textarea"));
    var button = form.querySelector("button[type=submit]");
    var status = form.querySelector(".form-status");
    form.setAttribute("novalidate", "");

    form.addEventListener("input", function (e) { if (e.target.getAttribute("aria-invalid") === "true") check(e.target); });
    fields.forEach(function (el) { el.addEventListener("blur", function () { if (el.value) check(el); }); });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var hp = form.querySelector("[name=website]");
      if (hp && hp.value) { form.classList.add("done"); return; }
      var say = function (t) { if (status) status.textContent = t; };
      var ok = fields.map(check).every(Boolean);
      if (!ok) {
        var bad = fields.find(function (f) { return f.getAttribute("aria-invalid") === "true"; });
        if (!bad.closest(".field")) say(msg(bad));     // a form without a slot under the field
        bad.focus();
        return;
      }
      button.disabled = true;
      say(FS.t("Sending…"));

      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data),
        credentials: "same-origin",
      }).then(function (res) {
        if (res.ok) { form.classList.add("done"); return; }
        button.disabled = false;
        if (res.status === 403 && window.turnstile) window.turnstile.reset(); // a token works once: get a new one
        if (res.status === 429) say(FS.t("Too many tries. Wait a minute and try again."));
        else if (res.status === 422) say(FS.t("Check the fields and try again."));
        else say(FS.t("Something went wrong. Try again or email me."));
      }, function () {
        button.disabled = false;
        say(FS.t("No connection. Try again."));
      });
    });
  });
});
