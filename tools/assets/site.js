// Theme. Light is the default; a reader can switch to dark, and the choice sticks.
(function () {
  "use strict";
  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;
  var root = document.documentElement;

  function paint() {
    var dark = root.dataset.theme === "dark";
    var label = dark ? "Switch to the light theme" : "Switch to the dark theme";
    button.setAttribute("aria-pressed", dark ? "true" : "false");
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
  }

  button.addEventListener("click", function () {
    var dark = root.dataset.theme !== "dark";
    root.dataset.theme = dark ? "dark" : "light";
    try {
      localStorage.setItem("theme", root.dataset.theme);
    } catch (e) {
      /* private mode: the choice lasts for this page only */
    }
    paint();
  });

  paint();
})();

// Pan-zoom for the chart panes. Hand-rolled, no dependency (see
// NOTES_viewer_decision.md). Without scripting the panes fall back to plain
// contained images, and the full-resolution file is one link away.
(function () {
  "use strict";
  var MAX = 8; // times the fit scale

  function setup(pane) {
    var img = pane.querySelector("img");
    if (!img) return;
    var iw = parseInt(img.getAttribute("width"), 10);
    var ih = parseInt(img.getAttribute("height"), 10);
    if (!iw || !ih) return;
    var s = 1, tx = 0, ty = 0, fit = 1;

    // Give the absolutely positioned image its intrinsic box before it loads:
    // a zero-size element never intersects, so a lazy image would never load.
    img.style.width = iw + "px";
    img.style.height = ih + "px";

    function apply() {
      img.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")";
    }

    function clampPan() {
      var pw = pane.clientWidth, ph = pane.clientHeight;
      var w = iw * s, h = ih * s;
      if (w <= pw) tx = (pw - w) / 2;
      else tx = Math.min(0, Math.max(pw - w, tx));
      if (h <= ph) ty = (ph - h) / 2;
      else ty = Math.min(0, Math.max(ph - h, ty));
    }

    var fitted = false;

    function refit(keep) {
      var pw = pane.clientWidth, ph = pane.clientHeight;
      if (!pw || !ph) return; // hidden pane: fit when it is revealed
      var atFit = !fitted || !keep || Math.abs(s - fit) < 1e-6;
      fit = Math.min(pw / iw, ph / ih);
      if (atFit) s = fit;
      s = Math.min(Math.max(s, fit), fit * MAX);
      fitted = true;
      clampPan();
      apply();
    }
    pane.refit = refit;

    function zoom(factor, cx, cy) {
      var ns = Math.min(Math.max(s * factor, fit), fit * MAX);
      tx = cx - (cx - tx) * (ns / s);
      ty = cy - (cy - ty) * (ns / s);
      s = ns;
      clampPan();
      apply();
    }

    pane.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = pane.getBoundingClientRect();
      zoom(Math.pow(1.0015, -e.deltaY), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });

    pane.addEventListener("dblclick", function (e) {
      var r = pane.getBoundingClientRect();
      zoom(s > fit * 1.01 ? fit / s : 2.5, e.clientX - r.left, e.clientY - r.top);
    });

    var drag = null;
    pane.addEventListener("pointerdown", function (e) {
      drag = { x: e.clientX, y: e.clientY };
      pane.classList.add("dragging");
      pane.setPointerCapture(e.pointerId);
    });
    pane.addEventListener("pointermove", function (e) {
      if (!drag) return;
      tx += e.clientX - drag.x;
      ty += e.clientY - drag.y;
      drag = { x: e.clientX, y: e.clientY };
      clampPan();
      apply();
    });
    function drop() { drag = null; pane.classList.remove("dragging"); }
    pane.addEventListener("pointerup", drop);
    pane.addEventListener("pointercancel", drop);

    pane.addEventListener("keydown", function (e) {
      var cx = pane.clientWidth / 2, cy = pane.clientHeight / 2, step = 60;
      var k = e.key;
      if (k === "+" || k === "=") zoom(1.4, cx, cy);
      else if (k === "-" || k === "_") zoom(1 / 1.4, cx, cy);
      else if (k === "0") { s = fit; clampPan(); apply(); }
      else if (k === "ArrowLeft") { tx += step; clampPan(); apply(); }
      else if (k === "ArrowRight") { tx -= step; clampPan(); apply(); }
      else if (k === "ArrowUp") { ty += step; clampPan(); apply(); }
      else if (k === "ArrowDown") { ty -= step; clampPan(); apply(); }
      else return;
      e.preventDefault();
    });

    window.addEventListener("resize", function () { refit(true); });
    refit(false);
  }

  var panes = document.querySelectorAll(".pane[data-panzoom]");
  for (var i = 0; i < panes.length; i++) setup(panes[i]);

  // The facsimile/redraw radios reveal a pane that was display:none at load,
  // so its first fit must wait until it has a size.
  var radios = document.querySelectorAll('.viewer input[type="radio"]');
  function refitAll() {
    for (var j = 0; j < panes.length; j++) panes[j].refit(true);
  }
  for (var i = 0; i < radios.length; i++) radios[i].addEventListener("change", refitAll);
})();
