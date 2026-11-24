/* 示例：把交互组件注册到 window.__GAMES__，引擎按 step.gameId 调用 */
(function () {
  window.__GAMES__ = window.__GAMES__ || {};

  /* 通用滑块实验：
     config: { target, min, max, step, tolerance } */
  window.__GAMES__["slider-demo"] = {
    mount: function (holder, api) {
      var cfg = api.config;
      var row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:12px;margin:16px 0";
      var lab = document.createElement("b");
      lab.textContent = "数值：";
      var input = document.createElement("input");
      input.type = "range";
      input.min = cfg.min; input.max = cfg.max; input.step = cfg.step; input.value = cfg.min;
      input.style.flex = "1";
      row.appendChild(lab); row.appendChild(input);
      holder.appendChild(row);

      var out = document.createElement("div");
      out.style.cssText = "font-size:14px;color:#4a5372";
      holder.appendChild(out);

      var solved = false;
      function update() {
        var v = parseFloat(input.value);
        var err = Math.abs(v - cfg.target);
        lab.textContent = "数值：" + v.toFixed(2) + "（目标 " + cfg.target + "）";
        out.textContent = err <= cfg.tolerance ? "✅ 进入目标范围" : "再调一调，误差 " + err.toFixed(2);
        if (err <= cfg.tolerance && !solved) {
          solved = true;
          api.done();
          api.toast("达成目标！");
        }
      }
      input.oninput = update;
      update();
    }
  };
})();
