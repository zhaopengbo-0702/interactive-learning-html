# 起步模板（学案 + 闯关，双形态）

把本目录整份拷到你的工作目录。这里演示“同一份 `data.json` 生成两件交付”。

## 1. 先让两件都跑起来

```powershell
cd starter
python build.py            # => dist/game.html（闯关）
python build_study.py      # => dist/study.html（学案）
```

用 `data.schema.json` 作示例数据；正式使用时复制成 `data.json` 再改：

```powershell
copy data.schema.json data.json
```

## 2. 改内容：只改 `data.json`

- `library`：学案正文（章节 → 小节 → 块）。这是**唯一事实源**；
- `levels`：闯关编排（关卡 → 步骤），阅读步骤引用同一个小节；
- `glossary`：术语小抄，两件共用；
- `meta`：`studyFile`/`gameFile` 决定两件交付的互相链接。

内容要改时只改 `library/glossary`，两件都重建。

## 3. 离线公式（两件都受益）

```powershell
curl -o tex-svg.js https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js
```

两个构建脚本都会自动内联，断网可用。

## 4. 审计两件交付

```powershell
python audit_deep.py  --src dist/game.html  --offline   # 闯关：全关卡全步骤
python audit_study.py --src dist/study.html --offline   # 学案：章节/公式/文本/锚点
```

两个都通过（bad=0 / 0 问题）再交付；交互通关用 `audit_interaction.js`。

## 5. 交付

- `dist/game.html`、`dist/study.html`、`README.md`；
- 数据源 `data.json`、两个构建脚本、两个审计脚本（便于维护）；
- 参考 `../../references/05-delivery.md` 与 `06-dual-mode.md`。

## 目录

```text
starter/
├─ template.html          闯关壳
├─ style.css              闯关样式
├─ engine.js              闯关引擎
├─ games.js               交互组件示例
├─ study_template.html    学案壳
├─ study.css              学案样式
├─ data.schema.json       双形态数据示例（复制为 data.json）
├─ build.py               闯关构建
├─ build_study.py         学案构建
├─ audit_deep.py          闯关审计
├─ audit_study.py         学案审计
└─ audit_interaction.js   交互通关审计骨架
```
