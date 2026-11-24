# -*- coding: utf-8 -*-
"""把 data.json 的 library 渲染成「学案」（文档形态）。

用法：
    python build_study.py
    python build_study.py --out dist/study.html
依赖：data.json（library/glossary/plan/tests/meta）、study_template.html、study.css
可选：tex-svg.js（离线 MathJax）
"""
import argparse
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_DEFAULT = "game.html"


def read(name):
    p = os.path.join(HERE, name)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def esc(s):
    return html.escape(s or "", quote=False)


def render_block(b):
    t = b.get("type")
    if t == "p":
        return "<p>" + b.get("html", "") + "</p>"
    if t == "h":
        return "<h3>" + b.get("html", "") + "</h3>"
    if t in ("list", "table"):
        return b.get("html", "")
    if t == "callout":
        return '<div class="callout ' + b.get("kind", "note") + '">' + b.get("html", "") + "</div>"
    if t == "code":
        return ('<pre><code class="language-' + esc(b.get("lang", "text")) + '">' +
                esc(b.get("code", "")) + "</code></pre>")
    if t == "formula":
        title = b.get("title", "")
        return ('<div class="formula"><div class="f-label">FORMULA</div>' +
                ("<div class=\"f-title\">" + title + "</div>" if title else "") +
                '<div class="f-body">$$' + b.get("tex", "") + "$$</div>" +
                ('<div class="f-explain">' + b.get("explain", "") + "</div>" if b.get("explain") else "") +
                "</div>")
    if t == "img":
        return ('<figure><img src="' + esc(b.get("src", "")) + '" alt="' + esc(b.get("alt", "")) + '">' +
                ("<figcaption>" + esc(b.get("caption", "")) + "</figcaption>" if b.get("caption") else "") +
                "</figure>")
    return b.get("html", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "dist", "study.html"))
    args = ap.parse_args()

    data = json.loads(read("data.json") or read("data.schema.json"))
    meta = data.get("meta", {})
    library = data.get("library", [])
    levels = data.get("levels", [])
    level_index = {lv["id"]: i + 1 for i, lv in enumerate(levels)}

    tpl = read("study_template.html")
    css = read("study.css")
    mathjs = read("tex-svg.js")

    if mathjs:
        math_cfg = (
            "<script>window.MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']]},"
            "options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']},"
            "svg:{fontCache:'local'}};</script>\n<script>" + mathjs + "</script>"
        )
    else:
        math_cfg = ""

    game_file = meta.get("gameFile", GAME_DEFAULT)
    sidebar, content = [], []
    for ch in library:
        sidebar.append('<div class="grp">' + esc(ch.get("title", "")) + "</div>")
        content.append('<section class="doc-section" id="' + esc(ch.get("id", "")) + '">' +
                       "<h2>" + ch.get("title", "") + "</h2>" +
                       ('<p class="sec-desc">' + ch.get("desc", "") + "</p>" if ch.get("desc") else ""))
        for sec in ch.get("sections", []):
            sid = sec.get("id", "")
            sidebar.append('<a href="#' + esc(sid) + '">' + esc(sec.get("title", "")) + "</a>")
            content.append('<section class="doc-section" id="' + esc(sid) + '" style="border:none;padding:18px 0 8px">')
            content.append("<h3>" + sec.get("title", "") + "</h3>")
            if sec.get("desc"):
                content.append('<p class="sec-desc">' + sec["desc"] + "</p>")
            for b in sec.get("blocks", []):
                content.append(render_block(b))
            ref_levels = (sec.get("refs") or {}).get("levels") or []
            if ref_levels:
                idx = level_index.get(ref_levels[0])
                if idx:
                    content.append('<a class="to-game" href="' + esc(game_file) + "#/L" + str(idx) +
                                   '" target="_blank" rel="noopener">去闯关练这一节 →</a>')
            content.append("</section>")
        content.append("</section>")

    game_link = ""
    if os.path.exists(os.path.join(HERE, "dist", game_file)) or game_file:
        game_link = '<a class="game-link" href="' + esc(game_file) + '" target="_blank" rel="noopener">🎮 打开闯关版</a>'

    script = ("<script>(function(){var links=[].slice.call(document.querySelectorAll('#side a'));"
              "var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));}).filter(Boolean);"
              "function hl(id){links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}"
              "if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)hl(e.target.id);});},{rootMargin:'-20% 0px -70% 0px'});secs.forEach(function(s){io.observe(s);});}"
              "})();</script>")

    out_html = (tpl.replace("__TITLE__", esc(meta.get("title", "学案")))
                   .replace("__SUBTITLE__", esc(meta.get("subtitle", "")))
                   .replace("__KICKER__", "STUDY GUIDE")
                   .replace("__DESC__", meta.get("subtitle", ""))
                   .replace("__VERSION__", esc(meta.get("version", "v1.0")))
                   .replace("__DATE__", datetime.date.today().isoformat())
                   .replace("__GAME_FILE__", esc(game_file))
                   .replace("__CSS__", css)
                   .replace("__MATHJAX__", math_cfg)
                   .replace("__SIDEBAR__", "\n".join(sidebar))
                   .replace("__CONTENT__", "\n".join(content))
                   .replace("__GAME_LINK__", game_link)
                   .replace("__SCRIPT__", script))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(out_html)
    print("written:", args.out)
    print("size: %.0f KB | chapters: %d | sections: %d" %
          (os.path.getsize(args.out) / 1024, len(library),
           sum(len(ch.get("sections", [])) for ch in library)))


if __name__ == "__main__":
    main()
