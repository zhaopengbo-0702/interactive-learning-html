# -*- coding: utf-8 -*-
"""学案（文档形态）审计：章节完整性、公式渲染、文本瑕疵、内部锚点。

用法：
    python audit_study.py --src dist/study.html
    python audit_study.py --src dist/study.html --offline
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
    [/：{2,}/, "double-colon"],
    [/[。，；、]\s*：/, "punct-colon"],
    [/。。|，，|；；/, "double-punct"],
    [/\*\*/, "md-bold"],
    [/undefined|\[object Object\]/, "undefined"],
    [/\uFFFD/, "replacement"],
    [/&lt;|&gt;|&amp;/, "entity"],
    [/\\\(|\\\)|\\begin\{|\\text\{|\\frac/, "raw-latex"],
    [/（\s*）|\(\s*\)/, "empty-paren"]
  ];
  (async function () {
    try {
      await sleep(800);
      try { if (window.MathJax && MathJax.startup && MathJax.startup.promise) await MathJax.startup.promise; } catch (e) {}
      await sleep(500);
      // 等公式排版稳定（最多 2 秒）
      for (var w = 0; w < 20; w++) {
        var probe = document.body.cloneNode(true);
        Array.prototype.forEach.call(probe.querySelectorAll("mjx-container,code,pre,script"), function (n) { n.remove(); });
        if ((probe.textContent || "").indexOf("$") < 0) break;
        await sleep(100);
      }
      var secs = document.querySelectorAll(".doc-section");
      var empty = 0;
      Array.prototype.forEach.call(secs, function (s) { if ((s.textContent || "").trim().length < 20) empty++; });
      var errCount = document.querySelectorAll("mjx-merror,[data-mjx-error]").length;
      var clone = document.body.cloneNode(true);
      Array.prototype.forEach.call(clone.querySelectorAll("mjx-container"), function (n) {
        n.parentNode.replaceChild(document.createTextNode("⟦公式⟧"), n);
      });
      Array.prototype.forEach.call(clone.querySelectorAll("code,pre"), function (n) {
        n.parentNode.replaceChild(document.createTextNode("⟦代码⟧"), n);
      });
      Array.prototype.forEach.call(clone.querySelectorAll("script,style"), function (n) { n.remove(); });
      var txt = (clone.textContent || "").replace(/\u00a0/g, " ");
      var raw = (txt.indexOf("$") >= 0) ? 1 : 0;
      var hits = [];
      RULES.forEach(function (r) {
        var m = r[0].exec(txt);
        if (m) hits.push(r[1] + " @ " + JSON.stringify(txt.slice(Math.max(0, m.index - 35), m.index + 55)));
      });
      // 内部锚点
      var broken = [];
      Array.prototype.forEach.call(document.querySelectorAll('a[href^="#"]'), function (a) {
        var id = a.getAttribute("href").slice(1);
        if (id && !document.getElementById(id)) broken.push(a.getAttribute("href"));
      });
      document.title = "STUDY " + JSON.stringify({
        sections: secs.length, empty: empty, err: errCount, raw: raw, hits: hits.slice(0, 12), broken: broken.slice(0, 8)
      });
    } catch (e) { document.title = "STUDY_FATAL " + e.message; }
  })();
})();
</script>
"""


def find_edge(explicit=None):
    if explicit:
        return explicit
    for p in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]:
        if os.path.exists(p):
            return p
    return "msedge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--edge", default=None)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    src = os.path.abspath(args.src)
    page = src + ".audit.html"
    open(page, "w", encoding="utf-8").write(open(src, encoding="utf-8").read().replace("</body>", AUDIT_JS + "</body>"))
    uri = "file:///" + page.replace("\\", "/")
    profile = tempfile.mkdtemp(prefix="audit-study-")
    cmd = [find_edge(args.edge), "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
           "--user-data-dir=" + profile, "--virtual-time-budget=60000", "--dump-dom", uri]
    if args.offline:
        cmd.insert(4, "--host-resolver-rules=MAP * 0.0.0.0")
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=180)
    except Exception as e:
        sys.exit("启动浏览器失败：%s" % e)
    dom = proc.stdout.decode("utf-8", "replace")
    m = re.search(r"<title>(.*?)</title>", dom, re.S)
    title = m.group(1) if m else ""
    print(title[:2000])
    if os.path.exists(page):
        os.remove(page)
    if not title.startswith("STUDY "):
        sys.exit(1)
    d = json.loads(title[6:])
    print("sections:", d["sections"], "| empty:", d["empty"], "| mathErr:", d["err"],
          "| raw$:", d["raw"], "| hits:", len(d["hits"]), "| broken anchors:", len(d["broken"]))
    ok = d["empty"] == 0 and d["err"] == 0 and d["raw"] == 0 and not d["hits"] and not d["broken"]
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
