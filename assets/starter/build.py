# -*- coding: utf-8 -*-
"""把 CSS / JS / 数据 / MathJax 组装成单文件学习网页。

用法：
    python build.py
    python build.py --out dist/course.html
约定：
    template.html   含 __CSS__ / __JS__ / __DATA__ / __MATHJAX__ / __TITLE__ 占位符
    style.css       主题样式
    engine.js       引擎
    games.js        可选：交互组件
    data.json       课程数据
    tex-svg.js      可选：内联 MathJax（离线公式）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    path = os.path.join(HERE, name)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def main():
    data = json.loads(read("data.json") or read("data.schema.json"))
    meta = data.get("meta") or {}
    default_out = os.path.join(HERE, "dist", meta.get("gameFile", "game.html"))

    ap = argparse.ArgumentParser()
    ap.add_argument("--debug", action="store_true", help="保留 test=1 解锁入口")
    ap.add_argument("--out", default=default_out)
    args = ap.parse_args()

    css = read("style.css")
    js = read("engine.js") + "\n" + read("games.js")
    tpl = read("template.html")
    if not tpl:
        sys.exit("缺少 template.html")

    title = (data.get("meta") or {}).get("title", "互动课程")

    # 可选：内联 MathJax（离线公式）。把 tex-svg.js 放在同目录即可。
    mathjs = read("tex-svg.js")
    if mathjs:
        cfg = (
            "<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],"
            "displayMath:[['$$','$$'],['\\\\[','\\\\]']]},"
            "options:{skipHtmlTags:['script','noscript','style','textarea','pre','code','summary']},"
            "svg:{fontCache:'local'},"
            "startup:{pageReady:function(){return MathJax.startup.defaultPageReady().then("
            "function(){document.documentElement.classList.add('math-ready');});}}};</script>\n"
            "<script>" + mathjs + "</script>"
        )
    else:
        cfg = ""

    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    if "$" in payload and not mathjs:
        print("[warn] 数据里有公式（$...$），但没有内联 MathJax："),
        print("       请把 tex-svg.js 放到本目录，或改用不含 $ 的占位文本。")
    html = (tpl.replace("__TITLE__", title)
               .replace("__CSS__", css)
               .replace("__MATHJAX__", cfg)
               .replace("__DATA__", payload)
               .replace("__JS__", js))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(html)
    size = os.path.getsize(args.out) / 1024
    levels = len(data.get("levels", []))
    steps = sum(len(lv.get("steps", [])) for lv in data.get("levels", []))
    print("written:", args.out)
    print("size: %.0f KB | levels: %d | steps: %d" % (size, levels, steps))


if __name__ == "__main__":
    main()
