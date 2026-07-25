# 案例：单页应用（极简模版）

一个小型模版案例，展示最简场景下的 SKILL 化过程。

## 输入

- **模版**：shadcn/ui 基础模版（只有一个 Index 页面）
- **对话历史**：无
- **模版规模**：小型（3 个业务文件）

## Phase 1 分析结果

### 技术栈

同奢侈品案例（React 18 + Vite 5 + TypeScript + Tailwind CSS 3 + shadcn-ui + pnpm）

### 骨架 vs 业务分类

**骨架**：同上（vite.config.ts, tsconfig.json, tailwind.config.ts, components/ui/*, lib/utils.ts, main.tsx）

**业务**：
- pages/Index.tsx（唯一页面）
- index.css（CSS 变量）
- App.tsx 中的路由部分

### 产品定义摘要

- **功能**：单页展示（无路由跳转、无状态管理、无数据层）
- **风格**：无明显风格（模版默认）

### 架构约束

- 路由：只有 `/`
- 状态：无 Context/Store
- 类型：无共享类型
- Provider：QueryClientProvider > TooltipProvider > BrowserRouter

## Phase 2 产出结构

```
single_page_app_skill/
├── SKILL.md                     # 70 行
├── tasks/
│   ├── 01-generate-code.md      # 50 行
│   └── 02-verify.md             # 25 行
├── reference/
│   ├── CONTEXT.md               # 30 行
│   ├── pages/Index.tsx           # ~50 行
│   └── styles/index.css          # ~20 行
├── prompt-template.md            # 提示词模版
├── prompts/                      # 3 个即用型提示词
│   ├── prompt-1.md
│   ├── prompt-2.md
│   └── prompt-3.md
└── rules/
    ├── architecture.md           # 极简骨架
    └── design-system.md          # 推断规则
```

**reference/ 总行数**：约 100 行（小型模版，全量复制）

## 关键决策说明

### 与奢侈品案例的对比

| 方面 | 奢侈品电商 | 单页应用 |
|------|-----------|---------|
| 业务文件数 | 15 | 3 |
| reference/ 行数 | 1080 | 100 |
| 路由数 | 3 | 1 |
| 状态管理 | CartContext | 无 |
| 共享类型 | Product 等 | 无 |
| 组件数 | 7 | 0（全在页面内） |
| 推断规则复杂度 | 高（电商特有的价格/分类/货币） | 中（通用的配色/排版） |

### 单页应用的特殊处理

1. **无组件拆分约束**：architecture.md 不限定组件列表，只保留 Provider 层级
2. **01-generate-code.md 更短**：没有复杂的生成顺序，直接写一个页面即可
3. **推断规则更通用**：不涉及电商特有的品类/价格逻辑，只有配色和排版
4. **examples 展示场景多样性**：同一个极简骨架可以变成 dashboard，也可以变成着陆页

### 何时需要扩展骨架

如果下游用户需要多页面、状态管理等功能，应在 architecture.md 中注明：
> "如用户需求涉及多页面，可扩展路由和新增 pages/；如涉及共享状态，可新增 Context"

但不要预设这些结构——保持最小骨架。
