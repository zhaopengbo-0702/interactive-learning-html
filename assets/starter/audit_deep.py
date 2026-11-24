# -*- coding: utf-8 -*-
"""深度审计：遍历全部关卡步骤，检查渲染/公式/文本瑕疵。

前置：Edge 浏览器（Windows）或 Chrome；把待审 HTML 路径传给 --src。
用法：
    python audit_deep.py --src dist/course.html
    python audit_deep.py --src dist/course.html --offline --edge "C:\\...\\msedge.exe"
输出：控制台打印 JSON 摘要；退出码 0 表示通过。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

AUDIT_JS = r"""
<script>
(function () {
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  var RULES = [
    { n: "double-colon", re: /：{2,}/ },
    { n: "punct-colon", re: /[。，；、]\s*：/ },
    { n: "line-only-colon", re: /(^|\n)\s*[：:]\s*(?=\n|$)/ },
    { n: "double-punct", re: /。。|，，|；；/ },
    { n: "md-bold", re: /\*\*/ },
    { n: "undefined", re: /undefined|\[object Object\]/ },
    { n: "replacement", re: /\uFFFD/ },
    { n: "entity", re: /&lt;|&gt;|&amp;|&quot;|&#\d+;/ },
    { n: "raw-latex", re: /\\\(|\\\)|\\\[|\\\]|\\begin\{|\\text\{|\\frac/ },
    { n: "empty-paren", re: /（\s*）|\(\s*\)/ },
    { n: "colon-then-punct", re: /[：:]\s*[。，、；]/ },
    { n: "end-colon", re: /[：:]\s*$/ }
  ];
  function inspect() {
    var stage = document.getElementById("stage");
    var res = { empty: !stage.querySelector(".screen"), err: 0, raw: 0, hits: [] };
    res.err = stage.querySelectorAll("mjx-merror,[data-mjx-error],.MathJax_Error").length;
    var clone = stage.cloneNode(true);
    Array.prototype.forEach.call(clone.querySelectorAll("mjx-container"), function (n) {
      n.parentNode.replaceChild(document.createTextNode("⟦公式⟧"), n);
    });
    Array.prototype.forEach.call(clone.querySelectorAll("code,pre"), function (n) {
      n.parentNode.replaceChild(document.createTextNode("⟦代码⟧"), n);
    });
    Array.prototype.forEach.call(clone.querySelectorAll("script,style,button,input,canvas"), function (n) { n.remove(); });
    var txt = (clone.textContent || "").replace(/\u00a0/g, " ");
    if (txt.indexOf("$") >= 0) res.raw = 1;
    RULES.forEach(function (r) {
      var m = r.re.exec(txt);
      if (m) res.hits.push(r.n + " @ " + JSON.stringify(txt.slice(Math.max(0, m.index - 35), m.index + 55)));
    });
    return res;
  }
  (async function () {
    try {
      if (location.search.indexOf("test=1") < 0) location.href += "?test=1";
      await sleep(1200);
      try { if (window.MathJax && MathJax.startup && MathJax.startup.promise) await MathJax.startup.promise; } catch (e) {}
      await sleep(300);
      var E = window.__ENGINE__;
      if (!E) { document.title = "AUDIT_FATAL no-engine"; return; }
      var data = window.__COURSE__;
      var total = 0, out = [];
      for (var i = 0; i < data.levels.length; i++) {
        var lv = data.levels[i];
        var steps = lv.steps || [];
        for (var s = 0; s < steps.length; s++) {
          E.openLevel(i, s);
          await sleep(60);
          for (var w = 0; w < 12; w++) {
            var st = document.getElementById("stage");
            var cl = st.cloneNode(true);
            Array.prototype.forEach.call(cl.querySelectorAll("mjx-container,code,pre,script"), function (n) { n.remove(); });
            if ((cl.textContent || "").indexOf("$") < 0) break;
            await sleep(80);
          }
          total++;
          var r = inspect();
          if (r.empty || r.err || r.raw || r.hits.length) {
            out.push({ level: lv.id, step: s, label: steps[s].label || steps[s].title || "", err: r.err, raw: r.raw, hits: r.hits.slice(0, 4) });
          }
        }
      }
      document.title = "AUDIT " + JSON.stringify({ total: total, bad: out.length, sample: out.slice(0, 30) });
    } catch (e) { document.title = "AUDIT_FATAL " + e.message; }
  })();
})();
</script>
"""


def find_edge(explicit):
    if explicit:
        return explicit
    for p in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]:
        if os.path.exists(p):
            return p
    return "msedge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--edge", default=None)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--timeout", type=int, default=600000)
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    page = src + ".audit.html"
    html = open(src, encoding="utf-8").read()
    open(page, "w", encoding="utf-8").write(html.replace("</body>", AUDIT_JS + "</body>"))

    uri = "file:///" + page.replace("\\", "/") + "?test=1"
    profile = tempfile.mkdtemp(prefix="audit-")
    cmd = [find_edge(args.edge), "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
           "--user-data-dir=" + profile, "--virtual-time-budget=" + str(args.timeout), "--dump-dom", uri]
    if args.offline:
        cmd.insert(4, '--host-resolver-rules=MAP * 0.0.0.0')
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=args.timeout / 1000 + 60)
    except Exception as e:
        sys.exit("启动浏览器失败：%s" % e)

    dom = proc.stdout.decode("utf-8", "replace")
    m = re.search(r"<title>(.*?)</title>", dom, re.S)
    title = m.group(1) if m else ""
    print(title[:2000])
    os.remove(page) if os.path.exists(page) else None
    if not title.startswith("AUDIT "):
        sys.exit(1)
    data = json.loads(title[6:])
    print("total:", data["total"], "bad:", data["bad"])
    sys.exit(0 if data["bad"] == 0 else 2)


if __name__ == "__main__":
    main()
