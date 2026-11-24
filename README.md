# interactive-learning-html

把论文、教材、PDF、笔记、课程或代码库整理为「完整学案 + 闯关式互动网页」的 AI 技能，附设计方法、起步模板、构建脚本和审计清单。

学案用于系统阅读、查阅与打印；闯关网页通过短卡片、题目和可操作实验推进学习。技能的方法论要求两种交付共享内容来源、双向链接，并核对术语、公式和关键数字。

视觉设计纳入制作与验收流程：先确定参考版式、配色、字体和版心，再设计封面与阅读组件，并检查桌面、手机、深色模式和打印效果。已有喜欢的旧版页面时，优先复用其 CSS、页面骨架与交互。

## 仓库内容

| 路径 | 内容 |
| --- | --- |
| [SKILL.md](SKILL.md) | 技能入口、工作流与验收要求 |
| [references/](references/) | 学习设计、内容流水线、双引擎架构、审计、交付、双形态与视觉设计 |
| [assets/starter/](assets/starter/) | HTML/CSS/JS 起步骨架、示例数据、Python 构建和审计脚本 |
| [assets/checklists/](assets/checklists/) | 构建、发布与视觉设计清单 |

视觉设计详见 [视觉规范](references/07-visual-design.md) 与 [设计检查清单](assets/checklists/design.md)。这些文件定义课程制作要求，starter 仍是起步骨架。

## 安装技能

将整个仓库克隆或复制到所用 AI 工具的技能目录，保持 `SKILL.md`、`references/` 和 `assets/` 的相对位置。

Codex 示例：

```powershell
git clone https://github.com/zhaopengbo-0702/interactive-learning-html.git "$env:USERPROFILE\.codex\skills\interactive-learning-html"
```

DeepSeek Harness 示例：

```powershell
git clone https://github.com/zhaopengbo-0702/interactive-learning-html.git "$env:USERPROFILE\.dsh\skills\interactive-learning-html"
```

若目录已经存在，请先核对本地内容，避免覆盖已有修改。按对应工具的说明刷新或重新启动后使用。

可使用这样的提示词：

> 使用 interactive-learning-html，把这份资料做成适合初学者的完整学案和闯关式学习网页。先整理知识体系与来源，再设计讲解、互动实验和自测，并核对两种交付的内容。

## 运行起步模板

构建需要 Python 3，使用标准库，无需安装 npm 依赖。建议先把 `assets/starter/` 复制到独立课程目录再修改。

```powershell
cd assets/starter
Copy-Item data.schema.json data.json
python build.py
python build_study.py
```

输出为 `dist/game.html` 和 `dist/study.html`，可用浏览器打开。未创建 `data.json` 时，两个脚本会读取 `data.schema.json`；该文件是示例课程数据，名称不代表 JSON Schema 验证规则。

将课程内容填入 `library`，在 `levels` 中编排关卡，在 `glossary` 中维护术语。修改数据后重新构建两种页面。

### 公式与离线使用

仓库未附带 MathJax。示例包含 TeX 公式，需将兼容的 `tex-svg.js` 放到 starter 目录后重建；构建脚本会内联该文件。

```powershell
curl.exe -L https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js -o tex-svg.js
python build.py
python build_study.py
```

该命令下载第三方依赖，需联网执行。正式交付前仍应断网检查公式及资源加载，并保留所使用依赖的许可信息。

### 审计

浏览器审计需要 Edge 或 Chrome，具体参数参见脚本的 `--help`。

```powershell
python audit_deep.py --src dist/game.html --offline
python audit_study.py --src dist/study.html --offline
```

`audit_interaction.js` 提供交互审计骨架，需要按课程组件补充驱动逻辑。

## 当前模板范围

已提供地图、依赖解锁、选择题、滑块实验、术语弹窗、XP/星级和浏览器本地存档；学案提供章节、侧栏与闯关互链。

`SKILL.md` 描述的是完整交付目标，starter 是需要继续开发的起步骨架。目前阅读卡仍使用关卡里的 `html`，尚未按 `sectionId` 自动从 `library` 生成；完整封面、搜索、阅读进度、深色模式、完整证书、计划与自测共享渲染、交叉一致性自动审计也需要补充。两种页面读取同一个数据文件，但尚不能据此认定所有内容已严格同源。

课程制作时，应补齐所需功能并执行完整审计；构建成功仅说明页面已生成。
