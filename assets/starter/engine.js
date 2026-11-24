/* ============================================================
 * 通用互动学习引擎（骨架）
 * 依赖：window.__COURSE__（数据）、可选 window.__GAMES__（交互组件）、
 *      可选 MathJax（公式排版）、可选 window.__GLOSSARY__
 * ============================================================ */
(function () {
  "use strict";
  var DATA = window.__COURSE__;
  var LEVELS = DATA.levels;
  var META = DATA.meta || {};
  var CHAPTERS = META.chapters || [];
  var KEY = META.storageKey || "course_v1";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  /* ---------- 状态 ---------- */
  var state = load();
  function load() {
    try { return Object.assign({ xp: 0, done: {}, stars: {} }, JSON.parse(localStorage.getItem(KEY) || "{}")); }
    catch (e) { return { xp: 0, done: {}, stars: {} }; }
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  /* ---------- 小工具 ---------- */
  var stage = $("#stage");
  var toastEl = $("#toast"), toastTimer = null;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }
  var cleanups = [];
  function onCleanup(fn) { cleanups.push(fn); }
  function runCleanups() {
    cleanups.forEach(function (f) { try { f(); } catch (e) {} });
    cleanups = [];
  }
  function setHud(title, pct) {
    $("#hudTitle").textContent = title;
    $("#hudFill").style.width = Math.max(0, Math.min(100, pct || 0)) + "%";
    $("#hudXp").textContent = state.xp + " XP";
  }

  /* ---------- MathJax：串行排队 ---------- */
  var mjQueue = Promise.resolve();
  function typeset() {
    if (!window.MathJax || !MathJax.typesetPromise) return;
    var ready = (MathJax.startup && MathJax.startup.promise) ? MathJax.startup.promise : Promise.resolve();
    mjQueue = mjQueue.then(function () { return ready; }).then(function () {
      try { return MathJax.typesetPromise([stage]); } catch (e) {}
    }).catch(function () {});
  }

  /* ---------- 解锁 ---------- */
  function levelUnlocked(i) {
    var lv = LEVELS[i];
    if (lv.require !== undefined) {
      if (lv.require === null) return true;
      if (Array.isArray(lv.require)) return lv.require.every(function (r) { return !!state.done[r]; });
      return !!state.done[lv.require];
    }
    return i === 0 || !!state.done[LEVELS[i - 1].id];
  }

  /* ---------- 步骤渲染 ---------- */
  var cur = null;
  var RENDER = {};

  function render() {
    runCleanups();
    var lv = LEVELS[cur.i], step = lv.steps[cur.s];
    var pct = lv.steps.length > 1 ? (cur.s / (lv.steps.length - 1)) * 100 : 0;
    setHud(lv.icon + " " + lv.title + (step.label ? " · " + step.label : ""), pct);
    stage.innerHTML = "";
    var box = el("div", "screen");
    stage.appendChild(box);
    (RENDER[step.type] || RENDER.story)(box, step, lv);
    typeset();
  }
  function next() {
    var lv = LEVELS[cur.i];
    if (cur.s < lv.steps.length - 1) { cur.s++; render(); }
    else finish();
  }
  function prev() { if (cur.s > 0) { cur.s--; render(); } }

  function actions(box, list) {
    var a = el("div", "actions");
    list.forEach(function (x) {
      var b = el("button", "btn " + (x.cls || "primary"), x.label);
      if (x.disabled) b.disabled = true;
      b.onclick = x.onClick;
      a.appendChild(b);
    });
    box.appendChild(a);
    return a;
  }

  RENDER.story = function (box, step) {
    var card = el("div", "card center");
    if (step.emoji) card.appendChild(el("div", "big-emoji", step.emoji));
    if (step.title) card.appendChild(el("h1", "screen-title", step.title));
    if (step.text) card.appendChild(el("p", "screen-text", step.text));
    box.appendChild(card);
    actions(box, [{ label: step.btn || "继续 ▶", onClick: next }]);
  };

  RENDER.quiz = function (box, step) {
    cur.quizTotal = (cur.quizTotal || 0) + 1;
    var card = el("div", "card");
    card.appendChild(el("div", "q", step.q));
    var opts = el("div", "opts");
    card.appendChild(opts);
    box.appendChild(card);
    var answered = false;
    step.options.forEach(function (o, i) {
      var b = el("button", "opt", '<span class="k">' + "ABCD"[i] + '</span><span>' + o + "</span>");
      b.onclick = function () {
        if (answered) return;
        answered = true;
        if (i === step.answer) { b.classList.add("correct"); cur.quizRight = (cur.quizRight || 0) + 1; }
        else {
          b.classList.add("wrong");
          opts.children[step.answer].classList.add("correct");
          cur.mistakes++;
        }
        Array.prototype.forEach.call(opts.children, function (x) { x.disabled = true; });
        if (step.explain) card.appendChild(el("div", "explain", (i === step.answer ? "✅ 答对了。" : "❌ 正确答案是 " + "ABCD"[step.answer] + "。") + step.explain));
        actions(box, [{ label: "继续 ▶", onClick: next }]);
      };
      opts.appendChild(b);
    });
  };

  RENDER.read = function (box, step) {
    var card = el("div", "card");
    var head = el("div", "read-head");
    head.appendChild(el("div", "badge", step.label || "阅读"));
    head.appendChild(el("div", "read-count", (step.i + 1) + " / " + step.total));
    card.appendChild(head);
    card.appendChild(el("div", "read-body", step.html));
    box.appendChild(card);
    actions(box, [
      { label: "← 上一页", cls: "ghost small", onClick: prev },
      { label: "继续 ▶", onClick: next }
    ]);
  };

  RENDER.game = function (box, step) {
    var card = el("div", "card");
    if (step.title) card.appendChild(el("h1", "screen-title", step.title));
    if (step.hint) card.appendChild(el("p", "screen-text", step.hint));
    var holder = el("div", "game-wrap");
    card.appendChild(holder);
    box.appendChild(card);
    var btn = null;
    var row = actions(box, [{ label: "继续 ▶", disabled: true, onClick: function () { if (!btn.disabled) next(); } }]);
    btn = row.querySelector("button");
    var impl = (window.__GAMES__ || {})[step.gameId];
    if (!impl) { holder.appendChild(el("p", "screen-text", "（缺少交互组件：" + step.gameId + "）")); return; }
    impl.mount(holder, {
      config: step.config || {},
      done: function () { btn.disabled = false; btn.classList.add("green"); btn.textContent = "完成，继续 ▶"; },
      mistake: function () { cur.mistakes++; },
      toast: toast,
      onCleanup: onCleanup,
      typeset: typeset,
      el: el
    });
  };

  RENDER.final = function (box, info, lv) {
    var card = el("div", "card center");
    card.appendChild(el("div", "big-emoji", "🏆"));
    card.appendChild(el("h1", "screen-title", "通关：" + lv.title));
    card.appendChild(el("div", "", "★".repeat(info.stars) + "☆".repeat(3 - info.stars)));
    card.appendChild(el("p", "screen-text", "获得 " + info.gain + " XP"));
    if (lv.card) card.appendChild(el("p", "screen-text", "知识卡：" + lv.card));
    box.appendChild(card);
    var idx = cur.i;
    actions(box, [
      idx + 1 < LEVELS.length ? { label: "下一关 ▶", cls: "green", onClick: function () { openLevel(idx + 1); } } : null,
      { label: "🗺️ 回到地图", cls: "ghost", onClick: showMap }
    ].filter(Boolean));
  };

  function openLevel(i, stepIdx) {
    if (!levelUnlocked(i)) { toast("先通关前面的关卡"); return; }
    cur = { i: i, s: Math.max(0, Math.min(stepIdx || 0, LEVELS[i].steps.length - 1)), mistakes: 0, quizRight: 0, quizTotal: 0 };
    runCleanups();
    render();
    window.scrollTo(0, 0);
  }

  function finish() {
    var lv = LEVELS[cur.i];
    var stars = Math.max(1, 3 - Math.min(2, cur.mistakes));
    var first = !state.done[lv.id];
    var gain = first ? (lv.xp || 80) : Math.round((lv.xp || 80) * 0.2);
    state.xp += gain;
    state.done[lv.id] = true;
    state.stars[lv.id] = Math.max(state.stars[lv.id] || 0, stars);
    save();
    runCleanups();
    setHud(lv.icon + " " + lv.title + " · 完成", 100);
    stage.innerHTML = "";
    var box = el("div", "screen");
    stage.appendChild(box);
    RENDER.final(box, { stars: stars, gain: gain }, lv);
    typeset();
  }

  function showMap() {
    runCleanups();
    setHud("🗺️ 关卡地图", 0);
    stage.innerHTML = "";
    var done = 0, stars = 0;
    LEVELS.forEach(function (l) { if (state.done[l.id]) { done++; stars += state.stars[l.id] || 0; } });
    var head = el("div", "map-head");
    head.innerHTML = "<h1>" + (META.title || "课程") + "</h1><p>" + (META.subtitle || "") + "</p>" +
      '<div class="badges"><span class="badge">' + state.xp + " XP</span> <span class=\"badge\">" + done + "/" + LEVELS.length + " 关</span> <span class=\"badge\">" + stars + " ★</span></div>";
    stage.appendChild(head);
    CHAPTERS.forEach(function (ch) {
      var list = LEVELS.filter(function (l) { return l.chapter === ch.id; });
      if (!list.length) return;
      var sec = el("div", "chapter");
      sec.appendChild(el("div", "chapter-head", "<span>" + ch.name + "</span><em>" + (ch.desc || "") + "</em>"));
      list.forEach(function (lv) {
        var idx = LEVELS.indexOf(lv);
        var unlocked = levelUnlocked(idx);
        var b = el("button", "level" + (unlocked ? "" : " locked"));
        b.innerHTML = '<div class="lv-ico">' + (unlocked ? lv.icon : "🔒") + "</div>" +
          '<div class="lv-body"><div class="lv-title">' + lv.title + '<span class="lv-tag"> ' + (lv.tag || "") + "</span></div>" +
          '<div class="lv-tag">' + (lv.desc || "") + "</div></div>" +
          '<div class="lv-right">' + "★".repeat(state.stars[lv.id] || 0) + "</div>";
        b.onclick = unlocked ? function () { openLevel(idx); } : function () { toast("先通关前面的关卡"); };
        sec.appendChild(b);
      });
      stage.appendChild(sec);
    });
    if (META.studyFile) {
      var foot = el("div", "map-foot");
      foot.style.cssText = "text-align:center;margin:28px 0 10px";
      foot.innerHTML = '<a class="btn ghost" href="' + META.studyFile +
        '" target="_blank" rel="noopener" style="text-decoration:none;display:inline-block">📖 打开完整学案</a>';
      stage.appendChild(foot);
    }
  }

  /* ---------- 术语小抄 ---------- */
  function showGlossary() {
    var data = window.__GLOSSARY__ || DATA.glossary || [];
    if ($("#glossary")) return;
    var wrap = el("div", "modal-wrap");
    wrap.id = "glossary";
    var card = el("div", "modal-card");
    var head = el("div", "modal-head");
    head.appendChild(el("div", "", "📖 术语小抄"));
    var close = el("button", "modal-close", "✕");
    head.appendChild(close);
    card.appendChild(head);
    data.forEach(function (g) {
      card.appendChild(el("div", "gloss-title", g.group));
      (g.items || []).forEach(function (it) {
        card.appendChild(el("div", "gloss-row",
          '<span class="gloss-sym">' + it[0] + '</span><span class="gloss-name">' + (it[1] || "") +
          '</span><span class="gloss-desc">' + (it[2] || "") + "</span>"));
      });
    });
    wrap.appendChild(card);
    document.body.appendChild(wrap);
    close.onclick = function () { wrap.remove(); };
    wrap.onclick = function (e) { if (e.target === wrap) wrap.remove(); };
  }

  /* ---------- 启动 ---------- */
  $("#homeBtn").onclick = showMap;
  var gb = $("#glossaryBtn");
  if (gb) gb.onclick = showGlossary;
  if (location.search.indexOf("test=1") >= 0) {
    LEVELS.forEach(function (l) { state.done[l.id] = true; });
  }
  // 延迟启动：确保同页的 games.js 先完成注册
  setTimeout(function () {
    var m = /^#\/?L(\d+)/.exec(location.hash || "");
    if (m && LEVELS[parseInt(m[1], 10) - 1]) openLevel(parseInt(m[1], 10) - 1);
    else showMap();
  }, 0);

  window.__ENGINE__ = { openLevel: openLevel, showMap: showMap, getState: function () { return state; } };
})();
