# 单文件学习应用架构

> 目标：一个 HTML 文件（或一个可整体拷走的目录），双击即用，离线可读，内容可重跑生成。

## 1. 总体结构

```text
┌───────────────────────────────┐
│ HUD：地图 / 标题 / 进度 / XP / 📖 小抄 / 音效 │
├───────────────────────────────┤
│ Stage：按 step 渲染（story/quiz/read/game/final）│
├───────────────────────────────┤
│ Actions：本步的操作按钮（继续/上一步/提交）      │
└───────────────────────────────┘
+ 轻量浮层：toast、modal（符号小抄）、fx（彩带）
```

数据与引擎分离：

```text
course.json ──▶ engine.js ──▶ 渲染
      ▲              ▲
  build_data.py   style.css / template.html
```

## 2. 数据 schema（最小可用）

```jsonc
{
  "meta": {
    "title": "课程标题",
    "storageKey": "course_v1",
    "chapters": [
      {"id": "ch1", "name": "第一章 · 名称", "desc": "一句话"}
    ]
  },
  "glossary": [
    {"group": "符号", "items": [["θ", "theta", "含义"]]}
  ],
  "levels": [
    {
      "id": "l1",
      "icon": "🎯",
      "title": "关卡标题",
      "tag": "可选小标签",
      "desc": "一句话介绍",
      "chapter": "ch1",
      "xp": 80,
      "require": null,          // null=随时可进；字符串=依赖关卡 id；数组=全部完成
      "card": "通关知识卡的一句话",
      "steps": [
        {"type": "story", "emoji": "🎯", "title": "标题", "text": "2–3 句"},
        {"type": "game", "title": "实验", "hint": "操作说明", "gameId": "slider-demo",
         "config": {"target": "…", "params": []}},
        {"type": "quiz", "q": "题干", "options": ["A","B","C","D"], "answer": 0, "explain": "解析"},
        {"type": "read", "label": "章节名", "html": "<p>卡片 HTML</p>"}
      ]
    }
  ]
}
```

扩展原则：新增关卡类型只需在引擎加一个 renderer；新增交互组件加一个 `gameId` 实现；schema 里只放参数，不放学科逻辑。

## 3. 引擎模块

1. **状态**：`{levelIndex, stepIndex, mistakes, quizRight, quizTotal}` + 存档。
2. **路由**：`#/L3`（可分享/调试），`?test=1` 解锁全部（仅调试用，交付可留但不要显眼）。
3. **渲染器表**：`story/quiz/read/game/final`，统一签名 `(stage, step, api)`。
4. **结算**：星级、XP（首通全额/重玩少量）、知识卡、解锁下一关。
5. **组件库**：滑块、点击画布、时间轴、拼图、参数扫描；统一注册 `onCleanup` 防止动画泄漏。
6. **浮层**：toast、modal、confetti；都做成可关、可键盘操作。
7. **数学排版**：统一入口 `typeset(stage)`，串行队列 + 等待 MathJax ready；对动态更新后的节点再次排版。
8. **错误兜底**：`window.onerror` 写入标题/浮层，方便自动化发现；单个组件异常不至于白屏。

## 4. 单文件 vs 目录版

| 场景 | 选择 |
|---|---|
| 要发给别人双击打开 | 单文件（CSS/JS/数据/MathJax 内联） |
| 需要频繁迭代/多人协作 | 目录版（build 脚本产出单文件） |
| 资源很大（视频/大图） | 目录版，资源用相对路径，整体打包 zip |

单文件体积预算：常规 <5 MB；内联 MathJax SVG 约 +2 MB；图多时用压缩/降分辨率。

## 5. 离线数学方案

- 下载 `mathjax@3.2.2/es5/tex-svg.js`（约 2 MB，无外部字体），内联到 `<head>`：
  ```html
  <script>window.MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']]},svg:{fontCache:'local'}};</script>
  <script>/* tex-svg.js 内容 */</script>
  ```
- 验证：屏蔽网络加载后，页面中应出现 `mjx-container` 且 `svg` 子节点；无 `data-mjx-error`；无残留 `$`。
- 若必须用 CDN：加备用 CDN + 加载失败提示 + 重试按钮，但不要假设用户一直联网。

## 6. 进度与版本

- `storageKey` 带版本号（`course_v1`），避免旧进度把新关卡顺序弄乱；
- 版本升级时可选迁移或提示“重置进度”；
- 精简版/完整版用不同 key，互不干扰。

## 7. 样式系统

- CSS 变量集中：背景/卡片/主色/强调色/圆角/阴影/字体；
- 两套主题（浅色默认，深色可选）；
- 移动端断点（≤560px）单列、字号、按钮尺寸；
- 内容区（read-body）单独一套排版：标题、列表、表格、代码、引用、公式溢出滚动。

## 8. 构建脚本职责

`build.py` 只做四件事：

1. 读 CSS/JS/数据/MathJax；
2. 注入 `template.html` 的占位符；
3. 转义数据中的 `</` 防止提前闭合 script；
4. 输出单文件并打印大小与数据统计。

**不要**在构建脚本里做内容转换；内容转换在 `build_data.py`。

## 9. 可维护性检查

- 换一个主题/领域，是否只改数据文件？是 → 架构合格；
- 加一种新交互，是否只加一个组件 + 一个 renderer 分支？是 → 合格；
- 内容更新后能否一条命令重建 + 审计？是 → 合格。


## 10. 双形态构建

同一份 `data.json` 产出两件交付：

```powershell
python build.py             # dist/game.html（闯关）
python build_study.py       # dist/study.html（学案）
```

- 学案引擎：侧栏目录 + 阅读进度 + 章节锚点 + 公式卡 + 表格/代码/提示框排版 + 打印样式 + Ctrl+K 搜索 + 每节“去闯关”链接；
- 闯关引擎：见上文；
- 交叉链接：`meta.studyFile` / `meta.gameFile`，两件交付页脚/地图底部互链；
- 两件交付共享 `glossary`、`library`、`tests`；
- 版本号 `meta.version` 同时显示在两边页脚。
