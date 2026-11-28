(function () {
  // The menu button says its state; the sheet closes on any tap inside it and on Escape.
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector(".nav__toggle");
  function setOpen(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (nav && toggle) {
    toggle.addEventListener("click", function () { setOpen(!nav.classList.contains("is-open")); });
    nav.querySelector(".nav__links").addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { setOpen(false); } });
  }
  // How long ago the page was checked.
  try {
    var t = document.getElementById("checked");
    var mins = Math.round((Date.now() - new Date(t.getAttribute("datetime")).getTime()) / 60000);
    if (isFinite(mins) && mins >= 0) {
      var hrs = Math.round(mins / 60), days = Math.round(mins / 1440), months = Math.round(days / 30.4);
      var text = mins < 1 ? "just now" : mins < 90 ? mins + " min ago" : hrs < 48 ? hrs + " h ago"
        : days < 60 ? days + " days ago" : months < 24 ? months + " months ago" : Math.round(days / 365) + " years ago";
      document.getElementById("ago").textContent = ", " + text;
    }
  } catch (e) {}
  // Times: UTC as written, or the reader's own zone when asked. The choice is kept for the next visit.
  // (Asked for in issue 5; the zone-name lookup follows pull request 7 by opsasa.)
  try {
    var times = document.querySelectorAll("time[data-t]");
    var buttons = document.querySelectorAll("[data-tz]");
    var note = document.getElementById("tz-note");
    var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var two = function (n) { return (n < 10 ? "0" : "") + n; };
    var zoneOf = function (d) {
      try {
        var parts = new Intl.DateTimeFormat("en-GB", { timeZoneName: "short" }).formatToParts(d);
        for (var p = 0; p < parts.length; p++) { if (parts[p].type === "timeZoneName") { return parts[p].value; } }
      } catch (e) {}
      var off = -d.getTimezoneOffset(), abs = Math.abs(off);
      return "UTC" + (off < 0 ? "-" : "+") + Math.floor(abs / 60) + (abs % 60 ? ":" + two(abs % 60) : "");
    };
    var differs = false;
    for (var i = 0; i < times.length; i++) {
      var el = times[i], next = el.nextElementSibling;
      el.setAttribute("data-utc", el.textContent);
      if (el.getAttribute("data-t") === "log" && next) { next.setAttribute("data-utc", next.textContent); }
      if (new Date(el.getAttribute("datetime")).getTimezoneOffset() !== 0) { differs = true; }
    }
    var show = function (local) {
      var zone = "";
      for (var i = 0; i < times.length; i++) {
        var el = times[i], kind = el.getAttribute("data-t"), next = el.nextElementSibling;
        var d = new Date(el.getAttribute("datetime"));
        if (!local || !isFinite(d.getTime())) {
          el.textContent = el.getAttribute("data-utc");
          if (kind === "log" && next) { next.textContent = next.getAttribute("data-utc"); }
          continue;
        }
        zone = zoneOf(d);
        var clock = two(d.getHours()) + ":" + two(d.getMinutes());
        var day = d.getDate() + " " + MONTHS[d.getMonth()];
        if (kind === "log") {
          el.textContent = (el.getAttribute("data-pre") || "") + clock;
          if (next) { next.textContent = day; }
        } else {
          el.textContent = clock + (kind === "clock-bare" ? "" : " " + zone) + (kind === "clock-day" ? " on " + day : "");
        }
      }
      for (var b = 0; b < buttons.length; b++) {
        buttons[b].textContent = local ? "Show UTC" : "Show local time";
        buttons[b].setAttribute("aria-pressed", local ? "true" : "false");
      }
      if (note) {
        note.textContent = local && zone
          ? "Times are in your time zone (" + zone + ")."
          : "Times are UTC.";
      }
    };
    // Where the reader's clock is UTC there is nothing to choose, and the buttons stay hidden.
    if (differs && buttons.length) {
      var KEY = "gta6race.times", local = false;
      try { local = window.localStorage.getItem(KEY) === "local"; } catch (e) {}
      for (var k = 0; k < buttons.length; k++) {
        buttons[k].hidden = false;
        buttons[k].addEventListener("click", function () {
          local = !local;
          try { window.localStorage.setItem(KEY, local ? "local" : "utc"); } catch (e) {}
          show(local);
        });
      }
      if (local) { show(true); }
    }
  } catch (e) {}
  // The look: the device decides unless the reader picks light or dark with the footer's button (issues 11
  // and 15). The choice lives in localStorage and is applied before first paint by a small script in the head.
  try {
    var themeBtn = document.querySelector("[data-theme-btn]");
    if (themeBtn) {
      var rootEl = document.documentElement, looks = ["auto", "light", "dark"];
      var schemeMeta = document.querySelector('meta[name="color-scheme"]');
      var tints = document.querySelectorAll('meta[name="theme-color"]');
      var readLook = function () { var v = rootEl.getAttribute("data-theme"); return v === "light" || v === "dark" ? v : "auto"; };
      var showLook = function (v) {
        if (v === "auto") { rootEl.removeAttribute("data-theme"); } else { rootEl.setAttribute("data-theme", v); }
        themeBtn.textContent = "Theme: " + v;
        if (schemeMeta) { schemeMeta.setAttribute("content", v === "auto" ? "light dark" : v); }
        for (var m = 0; m < tints.length; m++) {
          var own = tints[m].getAttribute("data-own") || tints[m].getAttribute("content");
          tints[m].setAttribute("data-own", own);
          tints[m].setAttribute("content", v === "auto" ? own : (v === "dark" ? "#1c1b16" : "#dfdedb"));
        }
      };
      themeBtn.addEventListener("click", function () {
        var next = looks[(looks.indexOf(readLook()) + 1) % looks.length];
        showLook(next);
        try { if (next === "auto") { localStorage.removeItem("gta6race.theme"); } else { localStorage.setItem("gta6race.theme", next); } } catch (e) {}
      });
      showLook(readLook());
      themeBtn.hidden = false;
    }
  } catch (e) {}

  // Filters over the standings (asked for in issues 12 and 13): a row stays when it meets every choice made.
  // The panel is hidden until this script runs, so there are no dead controls without it.
  try {
    var panel = document.getElementById("filter");
    var boardRows = document.querySelectorAll(".board > .board__row");
    if (panel && boardRows.length) {
      var picks = panel.querySelectorAll("select[data-f]");
      var shownNote = document.getElementById("filter-count");
      var clearBtn = document.getElementById("filter-clear");
      var noneNote = document.getElementById("filter-none");
      var applyFilters = function () {
        var shown = 0, active = false;
        for (var r = 0; r < boardRows.length; r++) {
          var keep = true;
          for (var s = 0; s < picks.length; s++) {
            var field = picks[s].getAttribute("data-f"), want = picks[s].value;
            if (!want) { continue; }
            active = true;
            var has = boardRows[r].getAttribute("data-" + field) || "";
            if (field === "os" || field === "gpu") {
              if ((" " + has + " ").indexOf(" " + want + " ") < 0) { keep = false; }
            } else if (!(parseInt(has, 10) >= parseInt(want, 10))) { keep = false; }
          }
          boardRows[r].hidden = !keep;
          if (keep) { shown++; }
        }
        if (shownNote) { shownNote.textContent = active ? "showing " + shown + " of " + boardRows.length : ""; }
        if (clearBtn) { clearBtn.hidden = !active; }
        if (noneNote) { noneNote.hidden = !(active && shown === 0); }
      };
      for (var q = 0; q < picks.length; q++) { picks[q].addEventListener("change", applyFilters); }
      if (clearBtn) {
        clearBtn.addEventListener("click", function () {
          for (var q = 0; q < picks.length; q++) { picks[q].value = ""; }
          applyFilters();
        });
      }
      panel.hidden = false;
      applyFilters();
    }
  } catch (e) {}
  // The estimate counts down between checks.
  try {
    ["fc-rel", "fc-short"].forEach(function (id) {
      var f = document.getElementById(id);
      if (!f) { return; }
      var hours = (new Date(f.getAttribute("data-target")).getTime() - Date.now()) / 3600000;
      if (!isFinite(hours)) { return; }
      var days = Math.round(hours / 12) / 2;
      var rel = hours < 0 ? "any time now" : hours < 12 ? "within hours" : hours < 36 ? "about a day"
        : "about " + (days % 1 ? Math.floor(days) + "½" : days) + " days";
      f.textContent = id === "fc-rel" ? rel.charAt(0).toUpperCase() + rel.slice(1) : rel;
    });
  } catch (e) {}
})();
