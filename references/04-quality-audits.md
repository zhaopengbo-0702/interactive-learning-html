# 审计：让“看起来没问题”变成“可以证明没问题”

> 单文件学习网页的 bug 大多不在逻辑，而在内容转换、渲染时序、模板残留。人眼抽查 10 页会漏掉 80%，所以必须脚本全量跑。

## 1. 审计金字塔（从便宜到贵，逐层通过）

| 层 | 检查 | 手段 | 通过线 |
|---|---|---|---|
| L1 语法 | JS/构建是否报错 | `node --check`、构建 stderr | 0 错 |
| L2 全量渲染 | 每个关卡每个步骤都能打开 | 无头浏览器遍历 | 0 异常、0 空白 |
| L3 公式 | 未渲染 `$`、MathJax 错误 | DOM 统计 | 0 |
| L4 文本 | 冒号悬空、重复标点、Markdown 残留、实体、丢字 | 正则规则集 | 0 |
| L5 交互 | 目标关卡能真实通关 | 脚本模拟点击/拖拽/输入 | 全部通过 |
| L6 离线 | 断网后核心内容可读、公式正常 | 屏蔽 DNS/网络 | 通过 |
| L7 人工 | 抽 10 页看排版/语气/难度 | 人 | 可接受 |

每次修改内容或引擎后，至少重跑 L2–L5；发布前跑 L1–L6。

## 2. 无头浏览器驱动方式（Windows / Edge）

```powershell
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$uri  = "file:///C:/path/to/course.html?test=1"
& $edge --headless --disable-gpu --no-sandbox --no-first-run `
  --user-data-dir="$env:TEMP\audit-profile" `
  --virtual-time-budget=120000 --dump-dom $uri > dom.html
```

要点：

- `--user-data-dir` 每次换新目录，避免锁；
- 想测离线：加 `--host-resolver-rules="MAP * 0.0.0.0"`；
- 截图：`--screenshot="x.png" --window-size=820,1200 --hide-scrollbars`；
- 长页面用 print-to-pdf 再逐页渲染图片看排版；
- 结果通过 `document.title` 回传（`--dump-dom` 后正则取 `<title>`），避免依赖控制台。

## 3. 全量渲染 + 公式审计脚本契约

注入页面的测试脚本要做：

1. 等 MathJax ready（`MathJax.startup.promise`），再遍历；
2. 对每个 level/step 调 `openLevel(i, s)`；
3. 等节点稳定（可轮询“stage 内没有未渲染 `$`”，最多 1–2 秒）；
4. 检查：
   - `.screen` 是否存在；
   - `stage.querySelectorAll("mjx-container")` 数量；
   - `[data-mjx-error]`/`mjx-merror` 数量；
   - 文本（克隆 DOM，移除 `mjx/code/pre/script`，把 `mjx` 替换成 `⟦公式⟧`）后跑规则集；
5. 汇总 `{total, bad, sample:[{id, step, label, hits}]}` 写入 `document.title`。

## 4. 文本规则集（直接可用）

```js
const RULES = [
  ["double-colon",      /：{2,}/],
  ["punct-colon",       /[。，；、]\s*：/],
  ["line-only-colon",   /(^|\n)\s*[：:]\s*(?=\n|$)/],
  ["double-punct",      /。。|，，|；；/],
  ["markdown-bold",     /\*\*/],
  ["undefined",         /undefined|\[object Object\]/],
  ["replacement-char",  /\uFFFD/],
  ["html-entity",       /&lt;|&gt;|&amp;|&quot;|&#\d+;/],
  ["raw-latex",         /\\\(|\\\)|\\\[|\\\]|\\begin\{|\\text\{|\\frac/],
  ["raw-dollar",        /\$/],
  ["empty-paren",       /（\s*）|\(\s*\)/],
  ["colon-before-punct",/[：:]\s*[。，、；]/],
  ["leading-punct",     /(^|\n)\s*[：:，,、；;]/,  // 题干/选项开头挂着一个冒号
  ["end-colon",         /[：:]\s*$/],   // 卡片以冒号结尾：多半是分页 bug
  ["start-punct",       /(^|\n)\s*[：:，。]/]
];
```

注意：检查文本前把行内代码替换成 `⟦代码⟧`、公式替换成 `⟦公式⟧`，否则会出现大量误报。
**特别容易漏**：选择题选项若渲染为 `<button>`，审计脚本不能把 button 整块删掉，否则选项文字（以及里面的 `**`、开头的冒号）全部进入盲区；应把 button 替换成它的 textContent 再检查。

## 5. 交互通关脚本契约

每个关卡配一个 driver（只对 game 关）：

```js
const drivers = {
  "slider-demo": async () => { setRange(slider, target); },
  "click-canvas": async () => { clickCanvas(0.9, 0.3); },
  "puzzle": async () => { clickTiles([...]); findBtn("检查").click(); },
  "play-animation": async () => { findBtn("开始").click(); await sleep(4000); }
};
```

流程：打开关卡 → 按 step 类型执行（story/read/paperIntro 点继续；quiz 选正确答案；game 调 driver）→ 检测通关文字/“下一关”按钮/证书 → 记录 `{id, ok, why}`。交付前必须全绿。

## 6. 常见故障 → 根因 → 修法

| 症状 | 根因 | 修法 |
|---|---|---|
| 公式显示成 `$...$` 源码 | MathJax 未加载/排版晚于检查 | 内联 MathJax；`typesetPromise` 后串行等待 |
| 公式渲染成空/嵌套错误 | 同一节点被排版两次 | 排版串行队列，等待 startup 完成 |
| 相邻公式变成 `$$` 展示式 | 两个 `$...$` 拼在一起 | 转换时检测 `$$` 并插空格 |
| 卡片以「：」结尾 | 分页把引导句和后续拆开 | 引导句不换卡；标题不落单 |
| 卡片开头丢字 | 解析器只序列化子元素，丢了 text 节点 | 补 `element.text`/tail |
| 正文出现 `**` | 静态 HTML 混入 Markdown | 清理星号 |
| 正文出现 `&lt;` | 双重转义 | 用文本节点而非手动转义 |
| 代码块变成普通段落 | 未识别围栏 | 先解析 fence 再转卡片 |
| 交互关无法通关 | 阈值过严/无提示 | 放宽阈值 + 方向提示 + 自动演示 |
| 离线时字体/公式缺失 | 依赖 CDN | 内联 MathJax SVG、系统字体栈 |
| 页面某些步空白 | 渲染抛异常被吞 | `window.onerror` 回传，修复异常组件 |

## 7. 内容覆盖审计

- 用覆盖矩阵逐项打勾（必须项 100%）；
- 抽查：随机 20 张卡与原文对照，确认数字、公式、结论未失真；
- 外部链接/工具版本标注“未核验”，交付说明写明边界。

## 8. 审计记录模板

```markdown
## 审计记录（YYYY-MM-DD）
- 构建版本：v1.2 / 文件 2.6MB
- L2 全量渲染：448 步，0 报错，0 空白
- L3 公式：0 未渲染，0 MathJax 错误
- L4 文本：0 问题
- L5 交互：9 个 game + 2 个资料关 + BOSS 全通过
- L6 离线：通过（DNS 屏蔽）
- 覆盖矩阵：必须项 100%
- 遗留：外链未核验（3 处）
```


## 9. 学案（文档形态）审计

`audit_study.py` 覆盖：

- 章节/小节数量与空节（`empty == 0`）；
- 公式：未渲染 `$`、MathJax 错误；
- 文本规则集（同闯关）；
- 内部锚点：所有 `href="#id"` 都能找到目标元素；
- 结果通过 `document.title` 回传，CLI 解析后打印 `sections / empty / mathErr / raw$ / hits / broken`。

两件交付的审计要一起跑：`audit_deep.py`（闯关）+ `audit_study.py`（学案）+ 交叉一致性（链接、术语、数字、覆盖）。
