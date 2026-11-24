/* 交互通关审计（通用骨架）
 *
 * 用法：把本文件内容注入到生成的 HTML 的 </body> 前，或作为独立脚本在页面加载后执行。
 *   1) 按你的 gameId 实现 drivers；
 *   2) 在浏览器（无头或有头）打开页面并附加 ?test=1；
 *   3) 读取 document.title 里的 "INTERACT ..." JSON。
 *
 * 命令行示例：
 *   msedge --headless --disable-gpu --no-sandbox --virtual-time-budget=300000 \
 *          --dump-dom "file:///.../course.audit.html?test=1"
 */
(function () {
  "use strict";
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function findBtn(t) { return $$("#stage button").find(function (b) { return (b.textContent || "").indexOf(t) >= 0; }); }
  function isClear() {
    return /通关：/.test(document.body.innerText) || !!findBtn("下一关") || !!document.querySelector(".cert");
  }

  /* ---------- 每个交互组件配一个 driver ---------- */
  var drivers = {
    "slider-demo": async function (step) {
      var input = document.querySelector("#stage input[type=range]");
      input.value = step.config.target;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      await sleep(120);
    }
    // "click-canvas": async function () { ... }
    // "puzzle": async function () { ... }
    // "play-animation": async function () { findBtn("开始").click(); await sleep(4000); }
  };

  async function playLevel(i) {
    var E = window.__ENGINE__;
    var lv = window.__COURSE__.levels[i];
    var steps = lv.steps || [];
    E.openLevel(i, 0);
    await sleep(150);
    for (var n = 0; n < steps.length + 6; n++) {
      if (isClear()) return { ok: true };
      var st = steps[n];
      if (!st) { await sleep(250); return { ok: isClear(), why: "no-step" }; }
      if (st.type === "story" || st.type === "read") {
        var b = findBtn("继续") || findBtn("开始") || $$("#stage .btn")[0];
        if (!b) return { ok: false, why: "no-next-btn" };
        b.click(); await sleep(140);
      } else if (st.type === "quiz") {
        var opts = $$("#stage .opt");
        if (!opts.length) return { ok: false, why: "no-opts" };
        opts[st.answer].click(); await sleep(110);
        var b2 = findBtn("继续"); if (b2) { b2.click(); await sleep(150); }
      } else if (st.type === "game") {
        var d = drivers[st.gameId];
        if (!d) return { ok: false, why: "no-driver:" + st.gameId };
        await d(st);
        var b3 = findBtn("完成，继续") || findBtn("继续");
        if (!b3 || b3.disabled) return { ok: false, why: "game-not-done:" + st.gameId };
        b3.click(); await sleep(170);
      } else {
        return { ok: false, why: "unknown-step:" + st.type };
      }
    }
    return { ok: isClear(), why: "timeout" };
  }

  (async function () {
    try {
      if (location.search.indexOf("test=1") < 0) location.href += "?test=1";
      await sleep(1500);
      try { if (window.MathJax && MathJax.startup && MathJax.startup.promise) await MathJax.startup.promise; } catch (e) {}
      var out = [];
      var levels = window.__COURSE__.levels;
      for (var i = 0; i < levels.length; i++) {
        if (!levels[i].steps.some(function (s) { return s.type === "game"; }) && levels[i].id !== "boss") continue;
        var r = await playLevel(i);
        r.id = levels[i].id;
        out.push(r);
      }
      document.title = "INTERACT " + JSON.stringify({ total: out.length, bad: out.filter(function (x) { return !x.ok; }).length, sample: out });
    } catch (e) { document.title = "INTERACT_FATAL " + e.message; }
  })();
})();
