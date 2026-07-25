---
name: template-to-skill
description: 将任意前端模版源码转化为可复用的 SKILL。输入模版目录（和可选的对话历史），输出一套完整的 SKILL 文件——让 AI 能根据用户提示词参考该模版的架构从头生成定制化产物。当用户说"把这个模版变成 skill"、"生成一个 skill"、"把代码封装成 skill"、"模版 SKILL 化"、"从这个项目提取 skill"时使用此技能。即使用户没有明确说"SKILL"，只要上下文是想把一份现有前端代码变成可复用的生成模式，都应使用。
---

# 模版 SKILL 化生成器

## 核心理念

产出的 SKILL 采用"定向修改"方法论——下游 AI 以 reference/ 源码为基础，先分析出结构层与内容层的边界，输出结构化的「定制清单」(Customization Manifest)，然后仅对清单中标注的内容层做精确替换，结构层保持原样。不是模板填空，也不是从头重写。

## 目标平台

产出的 SKILL 运行在 atoms.dev（详见 `references/atoms-platform.md`）。

核心约束：
- 骨架项目（Vite+React+TS+Tailwind+shadcn）由平台自动初始化，无需 SKILL 处理
- 产出的 SKILL 只描述"做什么"，不写平台工具调用语法（`Editor.write`/`Terminal.run` 等）
- 业务文件是创作目标：pages/、components/（非 ui）、data/、context/、styles

## 输入

支持两种输入模式：

### 模式 A：通过 chat_id 自动获取（适用于 atoms.dev 模版）

| 参数 | 必填 | 说明 |
|------|------|------|
| `chat_id` | 是 | atoms.dev 模版的 chat_id |
| `output_path` | 否 | 输出目录，默认 `~/Downloads/template-to-skill/<chat_id>_skill/` |

### 模式 B：直接提供文件路径

| 参数 | 必填 | 说明 |
|------|------|------|
| `template_path` | 是 | 模版源码目录路径（包含完整前端项目文件） |
| `conversation_path` | 否 | 对话历史文件路径（JSON 格式，记录模版创建过程的对话） |
| `output_path` | 否 | 输出目录，默认 `~/Downloads/template-to-skill/<目录名>_skill/` |

判断规则：
- 用户提供了 `chat_id` → 走模式 A
- 用户提供了源码目录路径或文件路径 → 走模式 B
- 两者都提供时，以显式路径为准（模式 B）

## 数据获取

### 模式 A：自动下载

收到 `chat_id` 后，自动执行以下脚本获取数据到 `~/Downloads/template-to-skill/<chat_id>/`：

```bash
# 1. 下载模版源码文件
python ~/.claude/skills/template-to-skill/scripts/download_chat_file.py <chat_id>
# → 保存到 ~/Downloads/template-to-skill/<chat_id>/source/

# 2. 获取对话历史
python ~/.claude/skills/template-to-skill/scripts/fetch_templates.py <chat_id>
# → 保存到 ~/Downloads/template-to-skill/<chat_id>/conversation.json
```

获取完成后，自动设置：
- `template_path` = `~/Downloads/template-to-skill/<chat_id>/source/`
- `conversation_path` = `~/Downloads/template-to-skill/<chat_id>/conversation.json`

### 模式 B：直接使用

用户提供的路径直接作为输入，跳过脚本下载步骤：
- `template_path` = 用户提供的源码目录
- `conversation_path` = 用户提供的对话历史文件（可选，没有则跳过对话分析）

## 执行流程

```
输入: chat_id 或 template_path(+conversation_path)
    ↓
Phase 0: 数据准备
  ┌─ 模式 A (chat_id): 运行脚本下载源码和对话历史
  │   ├─ download_chat_file.py → source/
  │   └─ fetch_templates.py   → conversation.json
  └─ 模式 B (路径): 直接使用用户提供的文件，跳过下载
    ↓
Phase 1: 分析 (tasks/01-analyze.md)
  产出 5 份内部文档:
  ┌─ 技术栈报告（框架/构建/文件分类）
  ├─ 产品定义（功能清单/视觉风格/数据结构/用户画像）
  ├─ 架构约束（固定骨架/自由空间）
  ├─ 逐文件定制化标注（每个业务文件的 🎨 可定制标注 → 写入 STRUCTURE_MAP.md）
  └─ 可定制点清单（从标注中汇总，哪些维度可根据提示词替换）
    ↓
⏸ 用户确认分析结果
    ↓
Phase 2: 生成 (tasks/02-generate.md)
  每个产出文件的信息来源:
  ┌─ SKILL.md          ← 产品定义 + 参数设计
  ├─ tasks/            ← 架构约束 + 定向修改方法论
  ├─ reference/        ← 源码（按大小策略裁剪，详见 02-generate.md §2.4）
  ├─ rules/            ← 架构约束 + 定制分析框架 + 编码规范
  ├─ prompt-template   ← 参数表 + 产品定义 + 设计推断
  └─ prompts/          ← prompt-template 实例化（≥1个演示扩展场景）
    ↓
Phase 3: 验证 (tasks/03-validate.md)
  - 文件完整性 + 内部引用一致性
  - reference/ 大小合理性
  - 产出 SKILL 可被下游 AI 正确消费
```

## 可定制点数据流

可定制点是模版中可以根据用户提示词替换/重新设计的部分（配色、数据、文案、分类等），不是"以后加什么功能"。

```
Phase 1 (§1.5 逐文件定制化标注)
  对每个业务文件标注可定制部分（🎨 可定制 / 📋 逻辑照搬 / 未标注不可动）
  产出: 逐文件标注（写入产出 SKILL 的 reference/STRUCTURE_MAP.md）
       ↓
Phase 1 (§1.6 识别可定制点)
  从 §1.5 的逐文件标注中汇总可定制维度
  产出: 可定制点清单（维度/当前值/定制方式）
       ↓
Phase 2 影响以下产出文件:
  ├─ reference/STRUCTURE_MAP.md → 逐文件标注（下游 AI 的核心执行指南）
  ├─ rules/architecture.md    → 可定制点表格 + 不可变骨架声明
  ├─ rules/design-system.md   → 推断规则（提示词关键词 → 设计决策）
  ├─ prompt-template.md       → "调整技巧"中提及可定制方向
  └─ prompts/                 → 3 个 prompt 展示不同定制方向
```

## 产出规范

```
<template_name>_skill/           # 默认位于 ~/Downloads/template-to-skill/<chat_id>_skill/
├── SKILL.md                  # 带 frontmatter 的入口文件
├── tasks/
│   ├── 01-generate-code.md   # 核心：参考式重跑（声明使用相同模版骨架）
│   └── 02-verify.md          # 构建验证
├── reference/
│   ├── CONTEXT.md            # 产品定义 + 视觉风格 + 数据结构
│   ├── STRUCTURE_MAP.md      # 逐文件定制化标注（🎨 可定制 / 📋 照搬 / 未标注不可动）
│   ├── pages/                # 参考页面
│   ├── components/           # 参考组件
│   ├── data/                 # 参考数据格式
│   └── styles/               # 参考样式
├── rules/
│   ├── architecture.md       # 骨架声明 + 可定制点 + 组件职责
│   └── design-system.md      # 设计推断规则 + 编码规范
├── prompt-template.md        # 用户可直接使用的提示词模版（带 {{变量}} 插值）
└── prompts/                  # 3 个即用型提示词文案（变量已填充）
    ├── prompt-1.md
    ├── prompt-2.md
    └── prompt-3.md
```

详细生成规范见 `rules/output-spec/` 目录。

## 注意事项

- 生成的 SKILL.md 必须带 YAML frontmatter（name + description）
- description 要写得"推送"一点，覆盖常见触发短语
- reference/ 中放原始代码，不加占位符
- 生成的 SKILL 的 tasks/01-generate-code.md 是最重要的文件——它决定下游 AI 的创作质量
- 产出的 SKILL 不包含项目初始化步骤——atoms.dev 的 `use_template` 已处理骨架初始化
- 产出的 SKILL 文件中不要出现平台工具名称（FrontendEngineer/Editor/Terminal/CheckUI），只描述"做什么"不描述"用什么工具做"
- 骨架 vs 业务文件判断标准详见 `tasks/01-analyze.md` §1.2
- Reference/ 包含所有业务文件完整源码（不做裁剪），详见 `tasks/02-generate.md` §2.4
